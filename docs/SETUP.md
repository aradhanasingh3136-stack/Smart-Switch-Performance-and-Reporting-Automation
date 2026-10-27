# Setup and reporting automation

## 1. Download and run

Download the repository ZIP and extract it, or clone the repository after publication. Open a terminal in the `smartswitch-analytics` folder. This is the folder containing `run.py`.

macOS or Linux:

```bash
python3 --version
python3 run.py --regenerate
python3 -m unittest discover -s tests -v
```

Windows PowerShell:

```powershell
py -3 --version
py -3 run.py --regenerate
py -3 -m unittest discover -s tests -v
```

Python must be version 3.10 or newer. No database server or pip installation is necessary. SQLite is included with Python.

The generator uses the fixed seed in `config.json`. The supplied period is 1 July to 28 September 2026. Regenerating replaces the synthetic raw CSVs. A regular run reads the current raw CSVs and replaces derived outputs.

## 2. Inspect the outputs

- `data/warehouse/smartswitch.sqlite`: local warehouse. Open it with a SQLite-compatible database viewer, or use Python's `sqlite3` module.
- `data/processed/`: clean facts, dimensions, daily metrics, firmware summaries and alert candidates.
- `reports/summary.json`: overall metrics.
- `reports/dashboard.svg`: visual report. Open in a browser.
- `reports/findings.md`: numbers, findings, actions and interpretation.
- `reports/data_quality.json`: source reconciliation and input hashes.
- `reports/rejected_rows.json`: invalid records and reasons.
- `reports/run_log.json`: local runtime and completion timestamp.

`python3 run.py --queries` prints the first eight rows of each analysis. Full queries are in `sql/03_analysis.sql`. The SQL dialect is SQLite. MySQL Workbench needs a MySQL server and cannot directly open this database. A future MySQL port would need dialect and loading changes.

## 3. Open Excel

Open `excel/SmartSwitch_Reporting.xlsx` in desktop Excel. It already contains the demo results, formulas, conditional formatting and a native chart. The sheets are Dashboard, Daily and Settings.

To enable automation:

1. Save a working copy as **Excel Macro-Enabled Workbook (`.xlsm`)**.
2. Open the Visual Basic editor. Use the Developer tab, or the editor shortcut available in your version.
3. Choose File → Import File and select `excel/SmartSwitchAutomation.bas`.
4. Return to Settings. In **B4**, enter the full repository folder. On Windows, an example is `C:\Projects\smartswitch-analytics`. On macOS, use the actual extracted folder path.
5. On Windows only, enter the full `python.exe` path in **B5**. The `RunPipelineAndRefresh` macro requires a path, not a shell command with arguments.
6. Run `RefreshDailyReport` to import the completed Python exports. Run `ExportDashboardPDF` to save a one-page PDF under `excel/exports/`.
7. On Windows, `RunPipelineAndRefresh` runs Python, waits for completion and refreshes Excel after a successful exit. On macOS run Python in Terminal first, then use `RefreshDailyReport`. macOS may request access to the selected files.

The VBA import checks headers and reconciliation before changing report values and restores Excel's application settings after errors. It is designed for this packaged **90-day** workbook. Changing the analysis period requires updating the workbook's row ranges and import contract. Python itself supports other positive day counts.

Review the module before enabling it. Excel for the web does not execute desktop VBA. The macro module is supplied as source and has not been executed in Excel in the preparation environment.

## 4. Open Power BI

Follow [the Power BI instructions](../powerbi/README.md). The project uses import-mode CSV sources. Power BI Desktop authoring requires Windows. On macOS the Python pipeline and exported reports can be used immediately; opening and validating the native PBIP requires a Windows environment with Desktop.

## 5. Schedule the Python report

### Windows Task Scheduler

Create a basic task named `SmartSwitch daily reporting`. Select a daily trigger, for example 08:00. Choose Start a program.

- Program: the full path to `python.exe`.
- Arguments: `"C:\Projects\smartswitch-analytics\run.py"`.
- Start in: `C:\Projects\smartswitch-analytics`.

Run the task manually once and check its last result plus `reports/run_log.json`. Choose a schedule and account appropriate to your machine. The demo refreshes the same fixed historical period; it does not create fresh live telemetry each day.

### macOS / Linux

Run `bash scripts/run_daily.sh` to check the wrapper. If using cron, edit `crontab -e` and add a line using your real Python and repository paths:

```cron
0 8 * * * /absolute/path/to/python3 /absolute/path/to/smartswitch-analytics/run.py >> /absolute/path/to/smartswitch-run.log 2>&1
```

The schedule refreshes the warehouse, CSVs and Python report. Excel macro execution and Power BI Desktop refresh are separate steps. Automated Power BI Service refresh of local files requires an appropriate gateway and service configuration, which are not provisioned by this repository.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `python3` is not recognized | Try `python` or `py -3` and check the version |
| Raw files are missing | Run with `--regenerate` |
| A conflicting duplicate is reported | Inspect the source key and resolve the conflicting export; do not discard arbitrarily |
| Device-hour coverage fails | Find missing hour/device keys before publishing connectivity rates |
| Power BI reports a missing folder | Update the DataFolder parameter and refresh |
| Workbook opens but no macros appear | Import the `.bas` module and save as `.xlsm` |
| Excel refresh says the row count differs | Restore the 90-day config or extend the workbook and VBA contract together |
| Git fails on macOS with an Xcode license prompt | Review and accept the license yourself, or use GitHub Desktop; this is a machine setup issue |
