# Data dictionary and metric contract

The dataset is a reproducible simulation. No household addresses, network identifiers, customer names, access tokens or real device traffic are included.

## Period and units

The default period is **2026-07-01 through 2026-09-28**, inclusive. Timestamps are local, timezone-naive **Asia/Kolkata** values, with no daylight-saving transition. A production multi-region ingestion system should preserve source timestamps and normalize to UTC before assigning local reporting dates.

One heartbeat is expected every five minutes: 12 per hour. All 60 devices are installed at the beginning of the period. The valid telemetry grid therefore contains 60 × 90 × 24 = **129,600 rows**, with **1,555,200 expected heartbeats**.

## Device dimension: `dim_device`

Grain: one switch. Primary key: `device_id`. Default rows: 60.

| Field | Type | Meaning |
|---|---|---|
| device_id | Text | Synthetic switch key, such as SW001 |
| home_id | Text | Synthetic home key, such as HOME001 |
| room | Text | Room served by the switch |
| load_type | Text | Lighting, Fan, Exhaust fan or Water heater |
| rated_watts | Number | Assumed connected load rating in watts |
| baseline_daily_hours | Number | Assumed daily runtime without the modeled reduction |
| installed_date | Date | Beginning of monitored eligibility |
| model | Text | Synthetic device model label |

Each home has three lighting switches rated at 24 W, 18 W and 12 W, a 65 W fan, a 40 W exhaust fan, and a 2,000 W water heater. These are scenario assumptions, not certified product specifications.

## Date dimension: `dim_date`

Grain: one day. Primary key: `date`. Default rows: 90. Other fields are `month` in YYYY-MM format, `weekday`, and `is_weekend` (0 or 1).

## Command fact: `fact_command`

Grain: one logical command request. Primary key: `command_id`. Valid default rows: 91,867.

| Field | Type | Meaning |
|---|---|---|
| command_id | Text | Stable logical command key |
| device_id | Text | Foreign key to device |
| event_time | Timestamp | Request timestamp in local IST |
| date | Date | Derived reporting day |
| firmware_version | Text | Firmware at command event time |
| source | Text | APP, VOICE or SCHEDULE |
| action | Text | ON or OFF |
| status | Text | SUCCESS, FAILED or TIMEOUT |
| failure_reason | Text | NONE, WIFI_OFFLINE, RELAY_ERROR or BROKER_TIMEOUT |
| latency_ms | Nullable number | Device acknowledgement latency in milliseconds, successful commands only |

Every record represents the final result of a logical command. Retries and individual transport attempts are not separately modeled. Duplicate CSV deliveries repeat the same logical record and are not extra requests.

SUCCESS requires a positive finite latency and NONE reason. Failed and timeout rows require null latency and a mapped failure reason. A SUCCESS acknowledgement does not confirm that the connected appliance physically changed state.

## Telemetry fact: `fact_device_hour`

Grain: one device-hour. Composite primary key: `(device_id, hour_start)`.

| Field | Type | Meaning |
|---|---|---|
| device_id | Text | Foreign key to device |
| hour_start | Timestamp | Exact start of the local hour |
| date | Date | Derived reporting day |
| firmware_version | Text | Firmware during that hour |
| expected_heartbeats | Integer | 12 in the default scenario |
| received_heartbeats | Integer | Count from 0 through expected |
| wifi_rssi_dbm | Number | Simulated received signal strength, negative dBm |
| on_hours | Number | Estimated relay-on duration, from 0 to 1 hour |
| estimated_kwh | Number | Rated watts × on_hours / 1,000 |

Hourly runtime is a modeled source estimate. It can be present during a cloud outage because local schedules can still run. It is not inferred from successful commands or calculated from missing cloud heartbeats. Command ON/OFF choices do not reconstruct runtime in this simulation.

## KPI definitions

| KPI | Definition | Exclusions / caution |
|---|---|---|
| Commands | Count of valid unique command IDs | Excludes quarantined rows and exact re-deliveries |
| Command success rate | Successes / commands | Success means acknowledgement |
| Mean ack latency | Sum successful latencies / successful commands | Never substitute zero for missing failed latency |
| P95 ack latency | Sorted successful latency at rank CEILING(0.95 × N) | Not interpolated; not an average of daily P95s |
| Heartbeat delivery | Sum received / sum expected | Connectivity proxy, not uptime |
| Estimated energy | Sum rated watts × estimated on_hours / 1,000 | No physical meter validation |
| Assumed baseline energy | Sum rated watts × baseline_daily_hours / 24 / 1,000 per eligible hour | Uses assumed runtime, constant across default days |
| Modeled avoided energy | Assumed baseline − estimated energy | May be negative; not clipped to zero |
| Modeled cost difference | Modeled avoided kWh × INR 8/kWh | Flat tariff assumption excludes slabs, fixed charges and taxes |
| Alert device-days | Distinct date-device records meeting at least one rule | Multiple reasons still count as one flagged device-day |

Fleet and rolling rates use summed numerators and denominators. Daily means are weighted by their successful command counts when calculating the fleet mean.

## Data quality and deduplication

The default raw command export contains 320 exact duplicates and five deliberately invalid rows. The telemetry export contains 180 exact duplicates. The loader quarantines invalid rows with reasons, removes exact re-deliveries, and stops on conflicting records sharing a valid key. A full valid device-hour grid is required before reporting heartbeat delivery.

`reports/data_quality.json` reconciles raw rows = accepted unique rows + exact duplicate rows + rejected rows for each source. `input_sha256` fingerprints the input files. Identical source files must produce identical reporting values.

## Alert rules

From `config.json`:

- `HEARTBEAT_LOSS`: device-day received / expected is below 99%.
- `COMMAND_RELIABILITY`: success is below 98% on a device-day with at least 25 commands.
- `WEAK_WIFI`: mean hourly RSSI is below −70 dBm.

These thresholds are explicit demonstration assumptions. They are not vendor SLAs or industry standards. The output is a candidate review list. No messages or device actions are triggered.
