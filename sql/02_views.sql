-- Facts are aggregated BEFORE joining to prevent command x telemetry fan-out.
CREATE VIEW v_command_daily AS
SELECT date, COUNT(*) commands,
 SUM(CASE WHEN status='SUCCESS' THEN 1 ELSE 0 END) successes,
 SUM(CASE WHEN status<>'SUCCESS' THEN 1 ELSE 0 END) failures,
 AVG(CASE WHEN status='SUCCESS' THEN latency_ms END) avg_latency_ms
FROM fact_command GROUP BY date;

CREATE VIEW v_telemetry_daily AS
SELECT t.date, SUM(expected_heartbeats) expected_heartbeats,
 SUM(received_heartbeats) received_heartbeats, SUM(estimated_kwh) estimated_kwh,
 SUM(d.rated_watts*d.baseline_daily_hours/1000.0/24.0) baseline_kwh,
 SUM(on_hours) on_hours, AVG(wifi_rssi_dbm) avg_rssi_dbm
FROM fact_device_hour t JOIN dim_device d USING(device_id) GROUP BY t.date;

CREATE VIEW v_daily_kpis AS
SELECT t.*, COALESCE(c.commands,0) commands, COALESCE(c.successes,0) successes,
 COALESCE(c.failures,0) failures, c.avg_latency_ms,
 1.0*c.successes/NULLIF(c.commands,0) command_success_rate,
 1.0*t.received_heartbeats/NULLIF(t.expected_heartbeats,0) heartbeat_delivery_rate,
 t.baseline_kwh-t.estimated_kwh estimated_avoided_kwh
FROM v_telemetry_daily t LEFT JOIN v_command_daily c USING(date);

CREATE VIEW v_device_daily AS
WITH c AS (
 SELECT date,device_id,COUNT(*) commands,
 SUM(CASE WHEN status='SUCCESS' THEN 1 ELSE 0 END) successes
 FROM fact_command GROUP BY date,device_id
), h AS (
 SELECT date,device_id,SUM(expected_heartbeats) expected_heartbeats,
 SUM(received_heartbeats) received_heartbeats, SUM(estimated_kwh) estimated_kwh,
 AVG(wifi_rssi_dbm) avg_rssi_dbm FROM fact_device_hour GROUP BY date,device_id
)
SELECT h.*,d.home_id,d.room,d.load_type,COALESCE(c.commands,0) commands,
 COALESCE(c.successes,0) successes,
 1.0*c.successes/NULLIF(c.commands,0) command_success_rate,
 1.0*h.received_heartbeats/h.expected_heartbeats heartbeat_delivery_rate
FROM h JOIN dim_device d USING(device_id) LEFT JOIN c USING(date,device_id);
