"""Export a compact, deterministic browser dataset with exact filtered P95 values."""
import json


def write_web_data(conn, root, cfg, quality):
    cursor = conn.execute("SELECT * FROM dim_device ORDER BY device_id")
    columns = [c[0] for c in cursor.description]
    devices = [dict(zip(columns, row)) for row in cursor]
    dates = [r[0] for r in conn.execute("SELECT date FROM dim_date ORDER BY date")]
    firmware = [r[0] for r in conn.execute("SELECT DISTINCT firmware_version FROM fact_device_hour ORDER BY firmware_version")]
    reasons = ["WIFI_OFFLINE", "RELAY_ERROR", "BROKER_TIMEOUT"]
    day_index = {day: i for i, day in enumerate(dates)}
    device_index = {d["device_id"]: i for i, d in enumerate(devices)}
    firmware_index = {v: i for i, v in enumerate(firmware)}
    groups = {}
    for day, device, fw, expected, received, energy, baseline, rssi, hours in conn.execute("""
        SELECT h.date,h.device_id,h.firmware_version,SUM(expected_heartbeats),
               SUM(received_heartbeats),SUM(estimated_kwh),
               SUM(d.rated_watts*d.baseline_daily_hours/24000.0),SUM(wifi_rssi_dbm),COUNT(*)
        FROM fact_device_hour h JOIN dim_device d USING(device_id)
        GROUP BY h.date,h.device_id,h.firmware_version ORDER BY h.date,h.device_id,h.firmware_version
    """):
        key = (day, device, fw)
        groups[key] = [day_index[day], device_index[device], firmware_index[fw], 0, 0, [],
                       [0, 0, 0], expected, received, round(energy, 6),
                       round(baseline, 8), round(rssi, 4), hours]
    for day, device, fw, status, reason, latency in conn.execute("""
        SELECT date,device_id,firmware_version,status,failure_reason,latency_ms
        FROM fact_command ORDER BY command_id
    """):
        row = groups[(day, device, fw)]
        row[3] += 1
        if status == "SUCCESS":
            row[4] += 1
            # Source latency has 0.1 ms precision. Preserve it without float drift.
            row[5].append(round(latency * 10))
        else:
            row[6][reasons.index(reason)] += 1
    for row in groups.values():
        row[5].sort()
    payload = {
        "schema_version": 1, "synthetic": True,
        "dates": dates, "devices": devices, "firmware": firmware, "failure_reasons": reasons,
        "targets": {"success": cfg["command_success_target"],
                    "heartbeat": cfg["heartbeat_delivery_target"]},
        "tariff_inr_per_kwh": cfg["tariff_inr_per_kwh"],
        "quality": {"duplicates": quality["duplicate_commands"] + quality["duplicate_telemetry"],
                    "rejected": quality["rejected_commands"] + quality["rejected_telemetry"]},
        "columns": ["date", "device", "firmware", "commands", "successes", "latency_tenths_ms",
                    "failures_by_reason", "expected_heartbeats", "received_heartbeats", "estimated_kwh",
                    "baseline_kwh", "rssi_sum", "device_hours"],
        "rows": list(groups.values()),
    }
    target = root / "web"
    target.mkdir(exist_ok=True)
    (target / "data.json").write_text(json.dumps(payload, separators=(",", ":"), allow_nan=False) + "\n")
