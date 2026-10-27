PRAGMA foreign_keys = ON;
CREATE TABLE dim_device (
 device_id TEXT PRIMARY KEY, home_id TEXT NOT NULL, room TEXT NOT NULL,
 load_type TEXT NOT NULL, rated_watts REAL NOT NULL CHECK(rated_watts > 0),
 baseline_daily_hours REAL NOT NULL CHECK(baseline_daily_hours BETWEEN 0 AND 24),
 installed_date TEXT NOT NULL, model TEXT NOT NULL
);
CREATE TABLE dim_date (
 date TEXT PRIMARY KEY, month TEXT NOT NULL, weekday TEXT NOT NULL, is_weekend INTEGER NOT NULL
);
CREATE TABLE fact_device_hour (
 device_id TEXT NOT NULL REFERENCES dim_device(device_id),
 hour_start TEXT NOT NULL, date TEXT NOT NULL REFERENCES dim_date(date),
 firmware_version TEXT NOT NULL, expected_heartbeats INTEGER NOT NULL CHECK(expected_heartbeats > 0),
 received_heartbeats INTEGER NOT NULL CHECK(received_heartbeats BETWEEN 0 AND expected_heartbeats),
 wifi_rssi_dbm REAL NOT NULL, on_hours REAL NOT NULL CHECK(on_hours BETWEEN 0 AND 1),
 estimated_kwh REAL NOT NULL CHECK(estimated_kwh >= 0),
 PRIMARY KEY(device_id, hour_start)
);
CREATE TABLE fact_command (
 command_id TEXT PRIMARY KEY, device_id TEXT NOT NULL REFERENCES dim_device(device_id),
 event_time TEXT NOT NULL, date TEXT NOT NULL REFERENCES dim_date(date), firmware_version TEXT NOT NULL,
 source TEXT NOT NULL CHECK(source IN ('APP','VOICE','SCHEDULE')),
 action TEXT NOT NULL CHECK(action IN ('ON','OFF')),
 status TEXT NOT NULL CHECK(status IN ('SUCCESS','FAILED','TIMEOUT')),
 failure_reason TEXT NOT NULL, latency_ms REAL,
 CHECK ((status = 'SUCCESS' AND latency_ms > 0 AND failure_reason = 'NONE') OR
        (status <> 'SUCCESS' AND latency_ms IS NULL AND failure_reason <> 'NONE'))
);
CREATE INDEX idx_command_date_device ON fact_command(date, device_id);
CREATE INDEX idx_hour_date_device ON fact_device_hour(date, device_id);
CREATE INDEX idx_command_firmware ON fact_command(firmware_version, date);
