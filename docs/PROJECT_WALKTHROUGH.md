# Understand and present the project

## The explanation in plain English

A smart switch can receive an instruction from an app, voice assistant or schedule. The device may acknowledge it quickly, respond slowly, fail, or time out. It also sends periodic heartbeats showing that the cloud is receiving messages from it.

This project simulates those records and answers operational questions. Python cleans and loads the data. SQL turns it into meaningful metrics. Power BI supports interactive analysis. Excel and VBA support a familiar daily reporting workflow.

The project is an **analytics and reporting system for home automation**. It is not a deployed smart home controller. You do not need electrical hardware to run it.

## Business problem

A support or product team receives complaints such as “the bedroom fan sometimes does not respond.” A single overall success percentage cannot tell them whether the problem is a particular device, a weak router signal, a home-wide outage, a voice-assistant delay or a firmware version.

The report helps a team prioritize investigation by home, device, source, date and firmware, while keeping estimated energy usage visible.

## Architecture in five steps

1. **Generate evidence.** The fixed-seed generator creates 60 devices in 10 homes over 90 days. Command volume is higher in morning and evening periods. Voice commands have a larger latency component. Weak-signal devices have more connectivity loss. Those are simulation design choices.
2. **Validate and load.** Python verifies keys, dates, categories, physical bounds and latency rules. Invalid rows go to quarantine. Exact duplicate deliveries are removed. Conflicting duplicate keys stop the run.
3. **Model in SQL.** SQLite stores dimensions plus two facts. Device-hour telemetry and commands have different grains, so the daily SQL views aggregate them separately before joining.
4. **Calculate and export.** SQL supplies counts and totals. Python calculates exact nearest-rank P95 and produces the findings, SVG dashboard, CSVs and candidate alerts.
5. **Present and refresh.** Power BI uses shared dimensions and DAX measures. Excel calculates daily rates and modeled energy differences. VBA imports exports, optionally starts Python on Windows, and exports a report PDF.

## The three stories to demonstrate

### A firmware regression

Every third switch enters firmware 1.1.0 on day 37, **7 August**, and remains on it through day 50, **20 August**. The simulation increases relay failures and acknowledgement latency during that period. A patch, version 1.1.1, appears from **21 August**.

Show the firmware comparison and the daily trend. Then explain the limitation: a before/after difference can reflect time and device mix. SQL Q8 compares rollout and control groups in matching pre and regression periods. Even that exercise is descriptive here because the whole dataset is generated.

### Connectivity incidents

HOME003 has a four-hour evening event on **1 August**. HOME008 has a seven-hour overnight event on **2 September**. Four switches have persistently weak simulated Wi-Fi. These patterns affect both heartbeat delivery and command reliability.

Show failure reasons, home filtering and device detail. Explain that a missing heartbeat can reflect transport loss or source loss; it does not by itself establish how long the switch was offline.

### An explicit energy baseline

From **28 August**, the model reduces runtime for lighting and exhaust fans. Estimated consumption uses load ratings and on-hours. Baseline consumption uses assumed normal daily hours. The total modeled difference is **211.4 kWh** for the period.

Do not attribute the entire baseline difference to the schedule change. The runtime generator includes variation and earlier differences from baseline. A causal savings claim would require metered observations, a defensible counterfactual, seasonal controls and an appropriate study design.

## Five-minute demonstration script

| Time | Show | What to say |
|---|---|---|
| 0:00–0:40 | README and dashboard | “I built a repeatable analytics workflow for synthetic smart home switches using SQL, Python, Power BI and Excel VBA.” |
| 0:40–1:20 | `config.json`, raw manifest | “The demo covers 60 devices, 10 homes and 90 days. A fixed seed makes the results reproducible.” |
| 1:20–2:00 | `data_quality.json`, tests | “The loader removes 500 exact duplicates, quarantines five bad records and rejects conflicting keys.” |
| 2:00–2:50 | SQL views and analysis Q8 | “The two fact tables have different grains. I aggregate before joining and compare firmware cohorts over matching windows.” |
| 2:50–3:40 | Native Power BI after acceptance checks | “Shared Home, Date and Firmware dimensions filter both facts. Rates use pooled counts and P95 uses command-level data.” |
| 3:40–4:25 | Excel and VBA module | “The workbook recalculates rates from daily totals. The macro imports validated CSVs and supports PDF reporting.” |
| 4:25–5:00 | Findings and limits | “The main demonstration is diagnosing a firmware regression and connectivity issues. Energy is a modeled estimate, and I would add metered data for real savings validation.” |

If Desktop or Excel macros have not been exercised, show their source and clearly describe their validation status. Use the generated dashboard as the verified visual report.

## A 60-second interview answer

“I built SmartSwitch Analytics to analyze reliability and usage for a simulated home automation fleet. I generated 90 days of data for 60 switches across 10 homes, including 91,867 commands and 129,600 device-hour records. Python validates and deduplicates the exports, and SQLite stores the two fact tables with shared dimensions. SQL produces daily KPIs and firmware comparisons. The project includes a Power BI report and an Excel VBA reporting workflow. The demo shows 98.01% command success and 614.4 milliseconds P95 acknowledgement time. My main modeling decisions were preventing fact-table fan-out, using weighted rates, and separating heartbeat delivery from true uptime. The data is synthetic, so I present the findings as a reproducible portfolio demonstration.”

## What to understand before using it on a resume

Run the project yourself, inspect one rejected record, read SQL Q2 and Q8, trace an Excel formula to its daily source, and verify a Power BI slicer once you have Desktop access. Be ready to explain each tool's responsibility and one limitation without reading the README aloud.
