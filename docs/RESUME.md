# Resume and portfolio wording

Use this after you have run the project, understood its design and verified the features you intend to discuss.

## Project entry

**Smart Switch Performance and Reporting Automation**<br>
SQL (SQLite), Python, Power BI, Excel VBA<br>
Personal portfolio project using synthetic IoT data

- Built a reproducible SQL and Python analytics pipeline for **91,867 simulated commands and 129,600 device-hour records** across 60 smart switches and 10 homes.
- Designed reporting for command reliability, P95 acknowledgement latency, heartbeat delivery, firmware performance and estimated energy usage using shared dimensions and correctly weighted KPIs.
- Implemented duplicate handling, invalid-record quarantine and reconciliation checks, with **12 automated tests** covering key data quality and metric behaviors.

After you verify the native Power BI report and VBA workflow yourself, a suitable additional bullet is:

- Developed a three-page Power BI report and an Excel VBA workflow to refresh validated daily metrics and export operational reports to PDF.

For a shorter resume, use the first bullet and the native-workflow bullet after verification.

## Two-line version

**SmartSwitch Analytics | SQL, Python, Power BI, Excel VBA**<br>
Analyzed 90 days of synthetic home automation events for 60 devices, with reproducible ETL, reliability KPIs, firmware comparisons and reporting automation. Added duplicate detection, record quarantine and 12 automated checks.

## Project link

Published repository URL:

`https://github.com/aradhanasingh3136-stack/Smart-Switch-Performance-and-Reporting-Automation`

The repository is public. Use this direct project link on your resume and portfolio.

Display text in the resume can be **GitHub: SmartSwitch Analytics**, linked to the verified repository URL. Avoid the profile's `?tab=projects` URL; a direct repository link takes a recruiter to the code and documentation.

## LinkedIn or portfolio description

“SmartSwitch Analytics is my home automation analytics portfolio project built with SQL, Python, Power BI and Excel VBA. It uses reproducible synthetic telemetry to examine command reliability, acknowledgement latency, connectivity, firmware performance and estimated energy consumption. The repository includes source code, data quality checks, reporting assets and a setup guide.”

## Claims to keep precise

| Prefer | Why |
|---|---|
| “Analyzed simulated commands” | The dataset is generated |
| “Detected a simulated firmware regression” | The scenario is injected by design |
| “Modeled energy difference” | There is no calibrated meter or validated counterfactual |
| “Automated data preparation and report exports” | The pipeline runs these steps |
| A measured local pipeline runtime, with machine and run context | This is observable technical performance |

Do not describe this as paid work for a company, a production fleet, a real customer deployment, a guaranteed energy saving, or a measured percentage reduction in manual reporting effort. No before/after manual reporting study was conducted.

The code should be committed using your authenticated GitHub account. The author section identifies you. There are no added co-author trailers or third-party author credits.
