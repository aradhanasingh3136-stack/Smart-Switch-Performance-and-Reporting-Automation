-- Run individually in DB Browser for SQLite, or: python run.py --queries
-- Q1. Fleet KPIs: ratios use matching pooled numerators and denominators.
SELECT COUNT(*) commands, SUM(status='SUCCESS') successes,
 ROUND(100.0*SUM(status='SUCCESS')/COUNT(*),2) success_pct,
 ROUND(AVG(CASE WHEN status='SUCCESS' THEN latency_ms END),1) mean_ack_ms
FROM fact_command;

-- Q2. Exact nearest-rank P95, no average of daily percentiles.
WITH ranked AS (
 SELECT latency_ms, ROW_NUMBER() OVER(ORDER BY latency_ms) rn,
 COUNT(*) OVER() n FROM fact_command WHERE status='SUCCESS'
)
SELECT MIN(latency_ms) p95_ms FROM ranked WHERE rn >= CAST((95*n+99)/100 AS INTEGER);

-- Q3. Failure contribution: operational prioritization.
SELECT failure_reason,COUNT(*) failures,
 ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER(),2) share_of_failures_pct
FROM fact_command WHERE status<>'SUCCESS' GROUP BY failure_reason ORDER BY failures DESC;

-- Q4. Firmware comparison is descriptive: rollout groups and dates differ.
SELECT firmware_version,COUNT(*) commands,
 ROUND(100.0*SUM(status='SUCCESS')/COUNT(*),2) success_pct,
 ROUND(AVG(CASE WHEN status='SUCCESS' THEN latency_ms END),1) mean_ack_ms
FROM fact_command GROUP BY firmware_version;

-- Q5. Rolling rate: sum the components, rather than average daily percentages.
SELECT date,command_success_rate,
 1.0*SUM(successes) OVER(ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)/
 NULLIF(SUM(commands) OVER(ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW),0) success_7d
FROM v_daily_kpis ORDER BY date;

-- Q6. Weak Wi-Fi cohorts: association, not proof of causality.
SELECT CASE WHEN avg_rssi_dbm < -70 THEN 'Weak' ELSE 'Healthy' END wifi_cohort,
 SUM(commands) commands,ROUND(100.0*SUM(successes)/SUM(commands),2) success_pct
FROM v_device_daily GROUP BY wifi_cohort;

-- Q7. Home exposure. Heartbeat loss is a connectivity proxy, not exact outage time.
SELECT d.home_id,ROUND(100.0*SUM(t.received_heartbeats)/SUM(t.expected_heartbeats),2) heartbeat_pct,
 ROUND(SUM(t.estimated_kwh),2) estimated_kwh
FROM fact_device_hour t JOIN dim_device d USING(device_id) GROUP BY d.home_id ORDER BY heartbeat_pct;

-- Q8. Matched treated/control time windows. Still observational, with simulated outcomes.
WITH cohorts AS (
 SELECT CASE WHEN CAST(SUBSTR(device_id,3) AS INTEGER)%3=0 THEN 'Rollout' ELSE 'Control' END cohort,
 CASE WHEN date<'2026-08-07' THEN 'Pre' ELSE 'Regression' END period,
 COUNT(*) n,SUM(status='SUCCESS') ok FROM fact_command
 WHERE date BETWEEN '2026-07-24' AND '2026-08-20' GROUP BY cohort,period
)
SELECT cohort,period,n,ROUND(100.0*ok/n,2) success_pct FROM cohorts;

-- Q9. Baseline comparison. A positive difference is modeled avoided consumption.
SELECT ROUND(SUM(estimated_kwh),2) estimated_kwh,ROUND(SUM(baseline_kwh),2) assumed_baseline_kwh,
 ROUND(SUM(estimated_avoided_kwh),2) modeled_avoided_kwh FROM v_daily_kpis;
