# Validation record

## Completed checks

| Area | Result | Evidence |
|---|---|---|
| Python pipeline | Completed on the packaged fixed-seed data | `reports/summary.json`, `reports/run_log.json` after a run |
| Automated unit/integration suite | 12 tests passed locally | `python3 -m unittest discover -s tests -v` |
| Deterministic reporting | 13 analytic exports byte-identical across a repeat run | `scripts/check_reproducibility.py` |
| GitHub Actions | Pipeline rebuild, all 12 tests and reproducibility check passed on Ubuntu with Python 3.12 | [Hosted validation run](https://github.com/aradhanasingh3136-stack/Smart-Switch-Performance-and-Reporting-Automation/actions/runs/40545115831), commit `c46fa30`, 27 October 2026 |
| SQL analyses | All nine queries executed | `python3 run.py --queries` |
| Source reconciliation | 92,192 raw commands = 91,867 valid + 320 duplicates + 5 rejected | `reports/data_quality.json` |
| Telemetry reconciliation | 129,780 raw rows = 129,600 valid + 180 duplicates | `reports/data_quality.json` |
| Relational checks | Zero foreign-key errors and complete default device-hour grid | Tests and quality report |
| P95 parity | SQL and Python both produce 614.4 ms | Percentile test |
| Excel workbook formulas | Recalculated with no matched formula errors in the authoring engine | Saved `.xlsx` with formulas and chart |
| Excel input changes | Changing a daily success count changes its rate; changing tariff from 8 to 10 increases modeled cost difference by 25% | Input-change checks performed and restored |
| Workbook presentation | All three sheets rendered and reviewed; clipped status text corrected | `reports/excel-dashboard.png` shows the main sheet |
| Power BI file schemas | 31 PBIP/PBIR-related files conformed to official Microsoft JSON schemas | Schema validation during preparation |
| Python visual report | SVG rendered and visually reviewed | `reports/dashboard.svg`, `reports/dashboard.png` |

The model contains 14 explicit DAX measures. Schema checks establish the structure of the report JSON files. The `model.bim` semantic model is JSON-authored; its full engine semantics require Desktop validation.

## Native application checks still required

- **Power BI Desktop:** open the project, set DataFolder, refresh all queries, evaluate measures, verify filters and visual rendering, save and reopen.
- **Desktop Excel VBA:** import the `.bas` module into a `.xlsm` working copy, run the refresh, exercise error paths and export the PDF.
- **Scheduled execution:** wrapper scripts are supplied; no task has been installed on your machine.
- **Physical devices:** no hardware, live MQTT service or measured electrical load was used.

These items are documented in their setup guides. Local Python and workbook checks should not be described as proof that these separate native workflows have passed.
