// Create a Text parameter named DataFolder containing the absolute data/processed path.

// Query: dim_device
let
    Source = Csv.Document(File.Contents(DataFolder & "/dim_device.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    MissingToNull = Table.ReplaceValue(Headers,"",null,Replacer.ReplaceValue,Table.ColumnNames(Headers)),
    Typed = Table.TransformColumnTypes(MissingToNull, {{"device_id", type text}, {"home_id", type text}, {"room", type text}, {"load_type", type text}, {"rated_watts", type number}, {"baseline_daily_hours", type number}, {"installed_date", type date}, {"model", type text}}, "en-US")
in
    Typed

// Query: dim_date
let
    Source = Csv.Document(File.Contents(DataFolder & "/dim_date.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    MissingToNull = Table.ReplaceValue(Headers,"",null,Replacer.ReplaceValue,Table.ColumnNames(Headers)),
    Typed = Table.TransformColumnTypes(MissingToNull, {{"date", type date}, {"month", type text}, {"weekday", type text}, {"is_weekend", Int64.Type}}, "en-US")
in
    Typed

// Query: fact_command
let
    Source = Csv.Document(File.Contents(DataFolder & "/fact_command.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    MissingToNull = Table.ReplaceValue(Headers,"",null,Replacer.ReplaceValue,Table.ColumnNames(Headers)),
    Typed = Table.TransformColumnTypes(MissingToNull, {{"command_id", type text}, {"device_id", type text}, {"event_time", type datetime}, {"date", type date}, {"firmware_version", type text}, {"source", type text}, {"action", type text}, {"status", type text}, {"failure_reason", type text}, {"latency_ms", type number}}, "en-US")
in
    Typed

// Query: fact_device_hour
let
    Source = Csv.Document(File.Contents(DataFolder & "/fact_device_hour.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    MissingToNull = Table.ReplaceValue(Headers,"",null,Replacer.ReplaceValue,Table.ColumnNames(Headers)),
    Typed = Table.TransformColumnTypes(MissingToNull, {{"device_id", type text}, {"hour_start", type datetime}, {"date", type date}, {"firmware_version", type text}, {"expected_heartbeats", Int64.Type}, {"received_heartbeats", Int64.Type}, {"wifi_rssi_dbm", type number}, {"on_hours", type number}, {"estimated_kwh", type number}}, "en-US")
in
    Typed
