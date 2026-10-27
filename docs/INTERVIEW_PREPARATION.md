# Interview preparation: 30 questions and suggested answers

Use these as explanations to understand, not a script to memorize. Describe completed work and validation accurately.

## Project and domain

### 1. Tell me about this project.

“SmartSwitch Analytics is a home automation reporting portfolio project using synthetic data. I built a Python and SQLite workflow for 60 switches across 10 homes over 90 days. It analyzes command reliability, acknowledgement latency, connectivity, firmware and estimated energy. It includes a Power BI project and an Excel VBA reporting workflow.” Follow with one technical decision and one finding.

### 2. Why did you choose a smart switch use case?

It combines event data, device telemetry, reporting automation and business interpretation. A device can respond slowly, miss heartbeats or fail after a firmware change. Those differences make the project more useful than simply counting events.

### 3. Is this real IoT data?

No. It is reproducible synthetic data from a fixed seed. I deliberately included household outages, weak-signal switches and a firmware regression. The goal is to demonstrate engineering and analytical methods without publishing customer information. I would validate the same methods with actual telemetry before claiming real operational impact.

### 4. Does your project control actual electrical switches?

No. It analyzes simulated command results and telemetry. A controller would require device integration, authentication, message delivery semantics, state confirmation and appropriate electrical hardware. Those are outside the completed project.

### 5. What is a heartbeat, and is heartbeat delivery the same as uptime?

A heartbeat is a periodic message from the device. Here the expected interval is five minutes. Delivery rate is received messages divided by expected messages. It is not exact uptime: message loss, broker issues or missing exports can also cause gaps. I retain a full eligible device-hour grid so missing rows cannot silently improve the rate.

### 6. What does successful command mean?

It means the simulated device acknowledgement was successful. It does not prove that the relay or appliance physically changed state. A production design could add a reported relay state or measured power response for stronger confirmation.

## SQL and modeling

### 7. What is the grain of each fact table?

`fact_command` contains one logical command ID. `fact_device_hour` contains one device-hour. The dimensions describe devices and dates. Power BI also has a firmware dimension shared by both facts. Stating the grain first prevents accidental double-counting.

### 8. Why not join the command fact directly to telemetry by device and date?

A device-day can contain many commands and 24 telemetry rows. A direct join multiplies those records and inflates counts or energy. I aggregate each fact independently to the intended daily grain, then join one daily result to the other. Alternatively I use shared dimensions and separate measures in Power BI.

### 9. Why is averaging daily success percentages wrong?

It weights each day equally regardless of volume. If one day has 1/1 successes and another 90/100, the daily-rate average is 95%, while the pooled rate is 91/101, about 90.10%. My fleet calculation uses total successes divided by total commands.

### 10. How do you calculate P95?

I sort successful command latencies and choose the value at rank `CEILING(0.95 × N)`. For 100 values, that is the 95th value. SQL uses `ROW_NUMBER` and `COUNT OVER`; Python uses the same rank rule. Power BI's DAX measure uses TOPN with a unique secondary command ID to break ties.

### 11. Why not average the daily P95 values?

A percentile depends on the underlying distribution, not just each group's percentile and count. Daily P95s discard most of the information required for a fleet P95. I compute it from the selected command-level values.

### 12. Which window functions did you use?

`ROW_NUMBER` and `COUNT OVER` identify the percentile rank. Windowed `SUM` calculates a rolling seven-day success rate from rolling successes and command totals. `SUM(COUNT(*)) OVER()` expresses each failure reason as a share of all failures.

### 13. Which indexes did you add, and why?

The primary keys protect logical command and device-hour uniqueness. Date-device indexes support date-filtered operations, and a firmware-date index supports firmware comparisons. For a larger warehouse I would inspect real query plans and benchmark selectivity rather than adding an index on every field.

### 14. Why use SQLite instead of a database server?

It makes the portfolio easy to reproduce with Python alone. It still supports relational constraints, indexes, views and the window functions used here. For concurrent ingestion or a large multi-user system, I would evaluate a server database or analytical warehouse. The current project does not claim a distributed architecture.

### 15. How do you preserve historical firmware information?

The facts store firmware as of the event/hour. A current firmware field on the device dimension alone would relabel old transactions after upgrades. For more complex changing attributes I would consider effective-dated dimensions and explicit event-time joins.

## Python and data quality

### 16. How do you handle duplicates?

I use stable business keys. Exact repeated rows are removed as re-deliveries. If two valid rows have the same key but different values, the load stops. I do not silently choose whichever row happened to arrive first.

### 17. What happens to bad data?

The validator checks identifiers, timestamps, enumerations, finite numeric values, heartbeat bounds and status-latency consistency. Invalid records are quarantined with a reason in `reports/rejected_rows.json`. Counts reconcile between raw, accepted, duplicate and rejected records.

### 18. Why are failure latencies null rather than zero?

There was no successful acknowledgement to measure. Zero would imply an instantaneous response and incorrectly improve the average or percentile. Failed commands remain in the reliability denominator while latency metrics use only successful acknowledgements.

### 19. Is your ETL idempotent?

It performs a deterministic full rebuild. Reprocessing unchanged raw files produces byte-identical reporting exports. The SQLite warehouse is built in a temporary database and replaces the previous database after success. This is a portfolio batch design, not an incremental event-processing guarantee.

### 20. What did you test?

The project has 12 unit/integration tests covering exact duplicates, conflicts, invalid-row quarantine, percentile edge cases, raw reconciliation, grid completeness, foreign keys, join inflation, pooled rates, SQL/Python percentile parity, energy arithmetic and null failure latency. A separate check confirms that 13 analytic exports remain byte-identical after a second run.

### 21. How would you scale the pipeline?

First profile memory, load time and query time. This version reads files into memory. For larger exports I would stream validation, use staging tables and batch inserts, partition retained history by event date where appropriate, and add incremental watermarks plus a late-arrival policy. I would keep source reconciliation and duplicate handling through the redesign.

### 22. How would you handle late-arriving events?

I would preserve both event time and ingestion time, use a replay window for recent dates, and deduplicate by stable keys. The reporting job would show its freshness and data completeness. The current fixed historical demo does not implement late-arrival ingestion.

## Power BI and Excel

### 23. Why use measures rather than calculated columns for KPIs?

Measures calculate in filter context and can respond to Home, Date and Firmware selections. A row-level calculated column does not correctly replace a pooled rate. I sum matching components inside each measure and divide at the selected scope.

### 24. What is the relationship direction in your Power BI model?

Each dimension filters each fact through a single-direction one-to-many relationship. There is no direct fact-to-fact relationship. I avoid bidirectional filtering because it can introduce unexpected paths and ambiguous filter behavior.

### 25. How does the Excel report refresh?

Python produces daily CSV exports. VBA loads and validates both the daily and overview files before replacing values in the reporting workbook. Existing formulas recalculate success rates and modeled energy differences. On Windows an optional macro launches Python and waits for it to finish. PDF export is another macro.

### 26. What is your VBA error-handling approach?

I use `Option Explicit`, validate file headers and row counts before updating, keep a copy of existing values, and restore screen updating, events and calculation mode after success or failure. A failed Python exit stops the refresh. A production release would also need native Excel tests, file locking decisions and a clearer audit trail.

### 27. Can the whole workflow run unattended?

The Python data preparation and report outputs can be scheduled. Excel automation and Power BI refresh have additional native application requirements. This repository does not provision a Power BI gateway or an unattended Office environment. I distinguish a runnable pipeline from those deployment steps.

## Interpretation and scenarios

### 28. Did the new firmware cause failures?

The regression is injected into the simulator, so its design is known. The report itself shows an association. With actual data I would compare comparable rollout and control groups over matching windows, check changes in connectivity and traffic mix, quantify uncertainty and consider a controlled rollout before claiming causality.

### 29. How did you calculate energy savings?

I call it a modeled energy difference. Consumption is rated watts multiplied by estimated on-hours divided by 1,000. Baseline uses an assumed number of daily hours. The difference is not verified savings. Real savings analysis needs actual metered readings and a credible baseline adjusted for relevant factors. The INR conversion is only a flat-tariff illustration.

### 30. What would you improve first in a real deployment?

I would establish source reliability and metric meaning: device acknowledgements versus physical state, actual heartbeat eligibility and gaps, and calibrated energy readings. Then I would add secure ingestion, retention, late-data handling, alert grouping and ownership, native report acceptance checks, and monitoring for job failures. Those improvements follow the current project's main limitations.

## Practice exercises

1. Add a duplicate command with a changed result and explain why the pipeline stops.
2. Calculate the fleet success percentage manually from the daily totals.
3. Explain the difference between median, mean and P95 using five sample latencies.
4. Show why an average of ratios and a ratio of sums differ.
5. Change the tariff from 8 to 10 in an Excel working copy and trace the formula change.
6. Run SQL Q8 and explain why even a matching-window comparison is not a complete causal study.
7. Filter the Power BI report to one home and verify totals against SQLite before calling the report validated.
