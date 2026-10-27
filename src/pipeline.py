"""Validate -> atomic SQLite rebuild -> aggregates -> reproducible exports."""
import csv
import hashlib
import json
import math
import os
import sqlite3
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from .generate_data import ROOT, write_csv


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def finite(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("non-finite number")
    return result


def clean_rows(rows, key_fields, validator):
    """Drop exact re-deliveries. Fail closed on conflicting versions of the same key."""
    seen, clean, rejected, duplicates = {}, [], [], 0
    for row in rows:
        try:
            normalized = validator(row)
        except (ValueError, KeyError, TypeError) as exc:
            rejected.append({"reason": str(exc), "row": row})
            continue
        key = tuple(normalized[k] for k in key_fields)
        if key in seen:
            if seen[key] != normalized:
                raise ValueError(f"Conflicting duplicate key: {key}")
            duplicates += 1
        else:
            seen[key] = normalized
            clean.append(normalized)
    return clean, rejected, duplicates


def percentile_nearest_rank(values, p=0.95):
    values = sorted(values)
    return values[math.ceil(p * len(values)) - 1] if values else None


def export_query(conn, query, path):
    cur = conn.execute(query)
    headers = [col[0] for col in cur.description]
    rows = cur.fetchall()
    write_csv(path, headers, rows)
    return [dict(zip(headers, row)) for row in rows]


def run_pipeline(root=ROOT):
    started = time.perf_counter()
    cfg = json.loads((root / "config.json").read_text())
    start = date.fromisoformat(cfg["start_date"])
    end = start + timedelta(days=cfg["days"])
    devices = read_csv(root / "data/raw/devices.csv")
    ids = {d["device_id"] for d in devices}
    if len(ids) != len(devices) or len(ids) != cfg["homes"] * cfg["switches_per_home"]:
        raise ValueError("Device dimension must have unique complete keys")

    def check_time(text, hourly=False):
        ts = datetime.fromisoformat(text)
        if ts.tzinfo is not None or not start <= ts.date() < end:
            raise ValueError("timestamp outside configured local IST period")
        if hourly and (ts.minute or ts.second or ts.microsecond):
            raise ValueError("telemetry must align to the hour")
        return ts

    def command(row):
        if row["device_id"] not in ids:
            raise ValueError("unknown device_id")
        ts = check_time(row["event_time"])
        if not row["command_id"] or row["status"] not in {"SUCCESS", "FAILED", "TIMEOUT"}:
            raise ValueError("invalid command key or status")
        if row["source"] not in {"APP", "VOICE", "SCHEDULE"} or row["action"] not in {"ON", "OFF"}:
            raise ValueError("invalid source or action")
        if row["firmware_version"] not in {"1.0.2", "1.1.0", "1.1.1"}:
            raise ValueError("unmapped firmware")
        latency = finite(row["latency_ms"]) if row["latency_ms"] != "" else None
        if row["status"] == "SUCCESS":
            if latency is None or latency <= 0 or row["failure_reason"] != "NONE":
                raise ValueError("success requires positive latency and NONE reason")
        elif latency is not None or row["failure_reason"] not in {"WIFI_OFFLINE", "RELAY_ERROR", "BROKER_TIMEOUT"}:
            raise ValueError("failure requires null latency and mapped reason")
        return {**row, "date": ts.date().isoformat(), "latency_ms": latency}

    def telemetry(row):
        if row["device_id"] not in ids:
            raise ValueError("unknown device_id")
        ts = check_time(row["hour_start"], hourly=True)
        expected, received = int(row["expected_heartbeats"]), int(row["received_heartbeats"])
        if expected != 60 // cfg["heartbeat_interval_minutes"] or not 0 <= received <= expected:
            raise ValueError("invalid heartbeat counts")
        rssi, on, energy = (finite(row[k]) for k in ["wifi_rssi_dbm", "on_hours", "estimated_kwh"])
        if not -100 <= rssi <= -20 or not 0 <= on <= 1 or energy < 0:
            raise ValueError("telemetry outside physical bounds")
        if row["firmware_version"] not in {"1.0.2", "1.1.0", "1.1.1"}:
            raise ValueError("unmapped firmware")
        return {**row, "date": ts.date().isoformat(), "expected_heartbeats": expected,
                "received_heartbeats": received, "wifi_rssi_dbm": rssi,
                "on_hours": on, "estimated_kwh": energy}

    raw_commands = read_csv(root / "data/raw/commands.csv")
    raw_hours = read_csv(root / "data/raw/telemetry.csv")
    commands, bad_c, dup_c = clean_rows(raw_commands, ["command_id"], command)
    hours, bad_h, dup_h = clean_rows(raw_hours, ["device_id", "hour_start"], telemetry)
    if len(hours) != len(devices) * cfg["days"] * 24:
        raise ValueError("Incomplete device-hour grid; cannot report a reliable heartbeat denominator")
    if not commands:
        raise ValueError("No valid command records")
    processed = root / "data/processed"
    reports = root / "reports"
    processed.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    db_dir = root / "data/warehouse"
    db_dir.mkdir(parents=True, exist_ok=True)
    tmp_db = db_dir / "smartswitch.building.sqlite"
    tmp_db.unlink(missing_ok=True)
    conn = sqlite3.connect(tmp_db)
    try:
        conn.executescript((root / "sql/01_schema.sql").read_text())
        conn.executemany("INSERT INTO dim_device VALUES (?,?,?,?,?,?,?,?)", [list(d.values()) for d in devices])
        dates = [start + timedelta(days=i) for i in range(cfg["days"])]
        conn.executemany("INSERT INTO dim_date VALUES (?,?,?,?)", [(d.isoformat(), d.strftime("%Y-%m"),
                             d.strftime("%A"), int(d.weekday() >= 5)) for d in dates])
        hc = ["device_id", "hour_start", "date", "firmware_version", "expected_heartbeats",
              "received_heartbeats", "wifi_rssi_dbm", "on_hours", "estimated_kwh"]
        cc = ["command_id", "device_id", "event_time", "date", "firmware_version", "source",
              "action", "status", "failure_reason", "latency_ms"]
        conn.executemany("INSERT INTO fact_device_hour VALUES (?,?,?,?,?,?,?,?,?)", [[r[k] for k in hc] for r in hours])
        conn.executemany("INSERT INTO fact_command VALUES (?,?,?,?,?,?,?,?,?,?)", [[r[k] for k in cc] for r in commands])
        conn.executescript((root / "sql/02_views.sql").read_text())
        if conn.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Foreign key validation failed")
        conn.commit()
        for table, order in [("dim_device", "device_id"), ("dim_date", "date"),
                             ("fact_command", "command_id"), ("fact_device_hour", "device_id,hour_start")]:
            export_query(conn, f"SELECT * FROM {table} ORDER BY {order}", processed / f"{table}.csv")
        daily = export_query(conn, "SELECT * FROM v_daily_kpis ORDER BY date", processed / "daily_kpis.csv")
        device_daily = export_query(conn, "SELECT * FROM v_device_daily ORDER BY date,device_id", processed / "device_daily.csv")
        fw = export_query(conn, """SELECT firmware_version,COUNT(*) commands,SUM(status='SUCCESS') successes,
            1.0*SUM(status='SUCCESS')/COUNT(*) success_rate,
            AVG(CASE WHEN status='SUCCESS' THEN latency_ms END) avg_latency_ms
            FROM fact_command GROUP BY firmware_version ORDER BY firmware_version""", processed / "firmware_kpis.csv")
        failures = export_query(conn, "SELECT failure_reason,COUNT(*) failures FROM fact_command WHERE status<>'SUCCESS' GROUP BY failure_reason ORDER BY failures DESC", processed / "failure_kpis.csv")
        n, ok = len(commands), sum(r["status"] == "SUCCESS" for r in commands)
        latency = [r["latency_ms"] for r in commands if r["status"] == "SUCCESS"]
        p95 = percentile_nearest_rank(latency)
        expected = sum(r["expected_heartbeats"] for r in hours)
        received = sum(r["received_heartbeats"] for r in hours)
        energy = sum(r["estimated_kwh"] for r in hours)
        baseline = sum(float(d["rated_watts"]) * float(d["baseline_daily_hours"]) / 1000 * cfg["days"] for d in devices)
        alerts = []
        for row in device_daily:
            reasons = []
            if row["heartbeat_delivery_rate"] < cfg["heartbeat_delivery_target"]:
                reasons.append("HEARTBEAT_LOSS")
            if row["commands"] >= cfg["daily_min_commands_for_alert"] and row["command_success_rate"] < cfg["command_success_target"]:
                reasons.append("COMMAND_RELIABILITY")
            if row["avg_rssi_dbm"] < cfg["weak_wifi_threshold_dbm"]:
                reasons.append("WEAK_WIFI")
            if reasons:
                alerts.append([row["date"], row["device_id"], row["home_id"], ";".join(reasons),
                               row["commands"], row["command_success_rate"], row["heartbeat_delivery_rate"],
                               "Check router placement" if "WEAK_WIFI" in reasons else "Review connectivity and firmware"])
        write_csv(processed / "alerts.csv", ["date", "device_id", "home_id", "alert_reasons", "commands",
                  "command_success_rate", "heartbeat_delivery_rate", "suggested_action"], alerts)
        summary = {"synthetic": True, "period_start": start.isoformat(), "period_end": (end-timedelta(days=1)).isoformat(),
                   "days": cfg["days"], "homes": cfg["homes"], "devices": len(devices),
                   "device_hour_rows": len(hours), "commands": n, "successes": ok, "failures": n-ok,
                   "command_success_rate": ok/n, "avg_latency_ms": sum(latency)/len(latency),
                   "p95_latency_ms": p95, "expected_heartbeats": expected, "received_heartbeats": received,
                   "heartbeat_delivery_rate": received/expected, "estimated_kwh": energy,
                   "assumed_baseline_kwh": baseline, "modeled_avoided_kwh": baseline-energy,
                   "modeled_cost_difference_inr": (baseline-energy)*cfg["tariff_inr_per_kwh"],
                   "alert_device_days": len(alerts), "firmware": fw, "failure_reasons": failures}
        (reports / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        # Fixed Excel import contract: 11 columns, 90 rows in the packaged demo.
        export_query(conn, """SELECT date,commands,successes,failures,expected_heartbeats,received_heartbeats,
                estimated_kwh,baseline_kwh,avg_latency_ms,command_success_rate,heartbeat_delivery_rate
                FROM v_daily_kpis ORDER BY date""", processed / "excel_daily.csv")
        write_csv(processed / "excel_overview.csv", ["metric", "value"], [
            ["p95_latency_ms", p95], ["tariff_inr_per_kwh", cfg["tariff_inr_per_kwh"]],
            ["devices", len(devices)], ["homes", cfg["homes"]]])
        quality = {"raw_commands": len(raw_commands), "accepted_commands": n, "duplicate_commands": dup_c,
                   "rejected_commands": len(bad_c), "raw_telemetry": len(raw_hours), "accepted_telemetry": len(hours),
                   "duplicate_telemetry": dup_h, "rejected_telemetry": len(bad_h),
                   "foreign_key_errors": 0, "device_hour_coverage": 1.0,
                   "input_sha256": {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((root/"data/raw").glob("*.csv"))}}
        (reports / "data_quality.json").write_text(json.dumps(quality, indent=2) + "\n")
        (reports / "rejected_rows.json").write_text(json.dumps(bad_c+bad_h, indent=2) + "\n")
        from .report import write_report
        write_report(root, summary, daily, fw, failures, cfg, quality)
    finally:
        conn.close()
    os.replace(tmp_db, db_dir / "smartswitch.sqlite")
    # Runtime is a local observation, never represented as business time saved.
    (reports / "run_log.json").write_text(json.dumps({"elapsed_seconds": round(time.perf_counter()-started,3),
         "completed_at_utc": datetime.now(__import__('datetime').timezone.utc).isoformat(),
         "status": "SUCCESS", "mode": "full deterministic rebuild"}, indent=2)+"\n")
    return summary
