# Operational findings

Synthetic demonstration, 2026-07-01 to 2026-09-28. These are generated observations, not customer results.

| Measure | Result | Interpretation |
|---|---:|---|
| Devices / homes | 60 / 10 | Fixed demo fleet |
| Valid command requests | 91,867 | One row per logical command |
| Command success | 98.01% | Successful device acknowledgement, not proof of physical actuation |
| P95 acknowledgement | 614.4 ms | Successful commands only, exact nearest-rank definition |
| Heartbeat delivery | 99.21% | Received / expected, not measured uptime |
| Estimated consumption | 2,070.08 kWh | Rated watts times estimated relay-on hours |
| Modeled avoided consumption | 211.42 kWh | Assumed baseline minus estimated consumption |

## Findings and actions

1. Firmware 1.1.0 has the lowest success rate: 91.70% across 4,758 commands. Investigate the simulated relay errors. Compare treated and control switches over matching dates using SQL Q8 before discussing causality.
2. RELAY_ERROR contributes 849 of 1,827 failures (46.5%). Inspect daily home connectivity and weak signal cohorts.
3. Firmware 1.1.1 has 98.25% success in its observed period. This is a descriptive comparison with a different time window and device mix.
4. The energy baseline is 2,281.50 kWh. The modeled difference of 211.42 kWh would correspond to INR 1,691.34 at an assumed flat INR 8.00/kWh. This excludes slabs, taxes and fixed charges, and is not a realized bill saving.
5. 935 device-days trigger at least one rule. This count is distinct flagged device-days, not incidents or notifications. Deduplication, ownership and suppression would be needed before operating alerts.

## Data quality

500 exact re-deliveries removed. 5 bad rows quarantined with reasons in `rejected_rows.json`. Both raw-to-clean row reconciliations balance. The complete device-hour grid preserves the expected-heartbeat denominator.
