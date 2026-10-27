"""Compare browser calculations with independent queries against the SQL facts."""
import json
import math
from pathlib import Path
import sqlite3
import subprocess

root = Path(__file__).resolve().parents[1]
cases = [{}, {"home": "HOME003"}, {"firmware": "1.1.0"},
         {"home": "HOME003", "start": "2026-07-30", "end": "2026-08-03"},
         {"home": "HOME008", "start": "2026-09-02", "end": "2026-09-02"},
         {"firmware": "1.1.0", "start": "2026-07-01", "end": "2026-07-02"},
         {"home": "HOME999"}, {"start": "2026-09-28", "end": "2026-07-01"}]
expected = []
with sqlite3.connect(root / "data/warehouse/smartswitch.sqlite") as db:
    for filters in cases:
        parts, values = [], []
        for key, column, operator in [("home", "d.home_id", "="), ("firmware", "f.firmware_version", "="),
                                      ("start", "f.date", ">="), ("end", "f.date", "<=")]:
            if key in filters:
                parts.append(f"{column} {operator} ?")
                values.append(filters[key])
        where = " WHERE " + " AND ".join(parts) if parts else ""
        commands = db.execute("SELECT f.status,f.latency_ms FROM fact_command f JOIN dim_device d USING(device_id)" + where, values).fetchall()
        latency = sorted(v for status, v in commands if status == "SUCCESS")
        hours, received, energy, baseline, count = db.execute("""
            SELECT COALESCE(SUM(f.expected_heartbeats),0),COALESCE(SUM(f.received_heartbeats),0),
                   COALESCE(SUM(f.estimated_kwh),0),
                   COALESCE(SUM(d.rated_watts*d.baseline_daily_hours/24000.0),0),COUNT(*)
            FROM fact_device_hour f JOIN dim_device d USING(device_id)
        """ + where, values).fetchone()
        n, ok = len(commands), len(latency)
        expected.append({"filters": filters, "expected": {"commands": n, "successes": ok,
            "successRate": ok/n if n else None, "p95": latency[math.ceil(.95*ok)-1] if ok else None,
            "heartbeatRate": received/hours if hours else None, "expected": hours, "received": received,
            "energy": energy, "baseline": baseline, "hours": count}})
subprocess.run(["node", str(root / "scripts/check_web_dashboard.mjs")],
               input=json.dumps(expected), text=True, cwd=root, check=True)
