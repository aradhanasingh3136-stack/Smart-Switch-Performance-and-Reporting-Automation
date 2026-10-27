"""Repeat the pipeline and check analytic outputs, excluding timestamped run logs."""
import hashlib
import subprocess
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
paths=[root/"reports/summary.json",root/"reports/data_quality.json"]
paths+=sorted((root/"data/processed").glob("*.csv"))
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
subprocess.run([sys.executable,"run.py"],cwd=root,check=True)
after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
if before != after: raise SystemExit("Reproducibility check failed")
print(f"PASS: {len(paths)} outputs are byte-identical after a second run")
