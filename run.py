#!/usr/bin/env python3
"""One-command demo. Uses Python 3.10+ standard library only."""
import argparse
import json
import sqlite3
from src.generate_data import ROOT, generate
from src.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regenerate", action="store_true", help="Recreate synthetic CSVs from the fixed seed")
    parser.add_argument("--queries", action="store_true", help="Print SQL analysis after refreshing")
    args = parser.parse_args()
    if args.regenerate or not (ROOT/"data/raw/commands.csv").exists():
        generate()
    summary = run_pipeline()
    print(json.dumps({k: summary[k] for k in ["devices", "commands", "command_success_rate", "p95_latency_ms", "heartbeat_delivery_rate"]}, indent=2))
    print("Outputs: reports/ | data/processed/ | data/warehouse/smartswitch.sqlite")
    if args.queries:
        with sqlite3.connect(ROOT/"data/warehouse/smartswitch.sqlite") as conn:
            for query in (ROOT/"sql/03_analysis.sql").read_text().split(";"):
                if query.strip() and any(s.strip() and not s.lstrip().startswith("--") for s in query.splitlines()):
                    cur = conn.execute(query)
                    print([col[0] for col in cur.description])
                    rows = cur.fetchall()
                    for row in rows[:8]:
                        print(row)
                    if len(rows)>8:
                        print(f"... {len(rows)} rows total")


if __name__ == "__main__":
    main()
