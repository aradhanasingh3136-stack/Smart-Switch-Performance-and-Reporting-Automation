"""Create portable and GitHub-ready archives without temporary or cached files."""
import argparse
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
GENERATED={"data/raw/commands.csv","data/raw/telemetry.csv","data/processed/fact_command.csv",
           "data/processed/fact_device_hour.csv","reports/run_log.json"}


def package(destination):
    destination.mkdir(parents=True,exist_ok=True)
    paths=[]
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file(): continue
        rel=p.relative_to(ROOT)
        if any(x in {".git","__pycache__",".venv",".pbi","node_modules"} for x in rel.parts): continue
        if p.suffix in {".pyc",".pyo",".xlsm"} or p.name.endswith(".inspect.ndjson") or p.name==".DS_Store": continue
        if p.suffix==".zip": continue
        paths.append((p,rel))
    for kind in ["complete","github-ready"]:
        target=destination/f"smartswitch-analytics-{kind}.zip"
        with zipfile.ZipFile(target,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=8) as archive:
            for path,rel in paths:
                if kind=="github-ready" and (rel.as_posix() in GENERATED or str(rel).startswith("data/warehouse/")): continue
                archive.write(path,Path(ROOT.name)/rel)
        print(f"{target.name}: {target.stat().st_size/1024/1024:.2f} MB")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=ROOT.parent)
    package(parser.parse_args().output.resolve())
