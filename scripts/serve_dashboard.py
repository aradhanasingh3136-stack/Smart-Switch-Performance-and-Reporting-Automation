"""Preview the interactive report at http://127.0.0.1:8765 (Ctrl+C to stop)."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if not (root / "web/data.json").exists():
    raise SystemExit("Run python3 run.py first to export the dashboard data.")
handler = partial(SimpleHTTPRequestHandler, directory=str(root / "web"))
print("SmartSwitch dashboard: http://127.0.0.1:8765", flush=True)
try:
    ThreadingHTTPServer(("127.0.0.1", 8765), handler).serve_forever()
except KeyboardInterrupt:
    print("\nDashboard preview stopped.")
