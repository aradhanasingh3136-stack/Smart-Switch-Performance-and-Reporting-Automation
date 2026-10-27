"""Deterministic demo telemetry. No real homes, credentials or device traffic."""
import csv
import json
import math
import random
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_csv(path, headers, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def firmware(day, device_no):
    if device_no % 3 == 0 and 37 <= day < 51:
        return "1.1.0"
    return "1.1.1" if day >= 51 else "1.0.2"


def generate(root=ROOT):
    config = json.loads((root / "config.json").read_text())
    rng = random.Random(config["seed"])
    start = datetime.fromisoformat(config["start_date"])
    expected = 60 // config["heartbeat_interval_minutes"]
    if config["heartbeat_interval_minutes"] <= 0 or 60 % config["heartbeat_interval_minutes"]:
        raise ValueError("Heartbeat interval must be a positive divisor of 60")
    loads = [("Living room", "Lighting", 24, 5.5), ("Bedroom", "Fan", 65, 9.0),
             ("Kitchen", "Exhaust fan", 40, 2.0), ("Bathroom", "Water heater", 2000, 0.8),
             ("Study", "Lighting", 18, 5.0), ("Balcony", "Lighting", 12, 4.0)]
    if config["switches_per_home"] != len(loads):
        raise ValueError("This demo defines exactly six load types per home")
    devices = []
    for home in range(1, config["homes"] + 1):
        for slot, (room, load, watts, baseline) in enumerate(loads):
            n = (home - 1) * len(loads) + slot + 1
            devices.append([f"SW{n:03}", f"HOME{home:03}", room, load, watts,
                            baseline, start.date().isoformat(), "SS-WIFI-16A"])
    write_csv(root / "data/raw/devices.csv", ["device_id", "home_id", "room", "load_type",
              "rated_watts", "baseline_daily_hours", "installed_date", "model"], devices)
    telemetry, commands = [], []
    cmd_no = 0
    for day in range(config["days"]):
        for dev in devices:
            device_id, home_id, room, load, watts, baseline, *_ = dev
            n = int(device_id[2:])
            fw = firmware(day, n)
            for hour in range(24):
                ts = start + timedelta(days=day, hours=hour)
                outage = ((home_id == "HOME003" and day == 31 and 18 <= hour < 22) or
                          (home_id == "HOME008" and day == 63 and 2 <= hour < 9))
                weak = n % 13 == 0
                rssi = round(max(-91, min(-35, rng.gauss(-76 if weak else -55, 4.5))), 1)
                received = 0 if outage else sum(rng.random() > (0.055 if weak else 0.004)
                                               for _ in range(expected))
                peak = 6 <= hour <= 9 or 18 <= hour <= 23
                # A schedule saves runtime after day 58. Baseline is an assumption, not a control group.
                intervention = 0.82 if day >= 58 and load in ("Lighting", "Exhaust fan") else 1.0
                shape = 1.65 if peak else 0.5357142857
                on_hours = min(1.0, baseline / 24 * shape * rng.uniform(0.68, 1.15) * intervention)
                # Local schedules can operate without cloud heartbeats; runtime remains estimated.
                energy = round(watts * on_hours / 1000, 6)
                telemetry.append([device_id, ts.isoformat(timespec="seconds"), fw, expected,
                                  received, rssi, round(on_hours, 6), energy])
                count = rng.choices([0, 1, 2, 3], [0.25, 0.43, 0.25, 0.07])[0] if peak else rng.choices([0, 1, 2], [0.65, 0.30, 0.05])[0]
                for _ in range(count):
                    cmd_no += 1
                    cts = ts + timedelta(seconds=rng.randrange(3600))
                    source = rng.choices(["APP", "VOICE", "SCHEDULE"], [0.48, 0.22, 0.30])[0]
                    if rng.random() > received / expected:
                        status, reason, latency = "TIMEOUT", "WIFI_OFFLINE", ""
                    elif rng.random() < (0.072 if fw == "1.1.0" else 0.006):
                        status, reason, latency = "FAILED", "RELAY_ERROR", ""
                    elif rng.random() < 0.003:
                        status, reason, latency = "TIMEOUT", "BROKER_TIMEOUT", ""
                    else:
                        status, reason = "SUCCESS", "NONE"
                        latency = round(rng.lognormvariate(math.log(245), 0.40) +
                                        (160 if source == "VOICE" else 0) +
                                        (240 if weak else 0) + (260 if fw == "1.1.0" else 0), 1)
                    commands.append([f"CMD{cmd_no:07}", device_id, cts.isoformat(timespec="seconds"),
                                     fw, source, rng.choice(["ON", "OFF"]), status, reason, latency])
    # Exact re-deliveries mimic an at-least-once export. The loader distinguishes conflicts.
    telemetry.extend([row[:] for row in rng.sample(telemetry, min(180, len(telemetry)))])
    commands.extend([row[:] for row in rng.sample(commands, min(320, len(commands)))])
    # Five deliberate bad rows, each quarantined with a reason.
    bad = [row[:] for row in commands[:5]]
    for i, row in enumerate(bad):
        row[0] = f"BAD{i:03}"
    bad[0][8] = -25
    bad[0][6:8] = ["SUCCESS", "NONE"]
    bad[1][1] = "SW999"
    bad[2][2] = "not-a-date"
    bad[3][6] = "UNKNOWN"
    bad[4][6:9] = ["SUCCESS", "NONE", ""]
    commands.extend(bad)
    rng.shuffle(telemetry)
    rng.shuffle(commands)
    write_csv(root / "data/raw/telemetry.csv", ["device_id", "hour_start", "firmware_version",
              "expected_heartbeats", "received_heartbeats", "wifi_rssi_dbm", "on_hours",
              "estimated_kwh"], telemetry)
    write_csv(root / "data/raw/commands.csv", ["command_id", "device_id", "event_time",
              "firmware_version", "source", "action", "status", "failure_reason", "latency_ms"], commands)
    manifest = {"synthetic": True, "timezone": "Asia/Kolkata", "timestamps": "local naive IST; no DST",
                "seed": config["seed"], "start_date": start.date().isoformat(),
                "days": config["days"], "devices": len(devices), "raw_commands": len(commands),
                "raw_telemetry": len(telemetry), "injected_invalid_rows": 5,
                "injected_exact_duplicates": 500,
                "scenarios": ["HOME003 day 31 evening outage", "HOME008 day 63 overnight outage",
                              "Firmware 1.1.0 regression days 37-50 on every third switch",
                              "Firmware 1.1.1 patch from day 51", "Reduced scheduled runtime from day 58"]}
    (root / "data/raw/manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2))
