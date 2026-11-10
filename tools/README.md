# Tools

## csv_to_kql.py

Turns a table library sample CSV into KQL you can run anywhere, so you can practise queries and test detections
with no populated workspace and no write permissions.

```bash
# A `let <Table> = datatable(...)` block to paste above your query (Log Analytics, Sentinel or ADX)
python3 tools/csv_to_kql.py sentinel/tables/SigninLogs/SigninLogs_sample.csv

# Same, with timestamps moved so the newest row is "now" (so ago() filters match the sample)
python3 tools/csv_to_kql.py sentinel/tables/SigninLogs/SigninLogs_sample.csv --rebase

# Azure Data Explorer `.create table` and `.ingest inline` commands for a free cluster
python3 tools/csv_to_kql.py sentinel/tables/SigninLogs/SigninLogs_sample.csv --mode adx
```

Column types come from the table's README schema, so columns such as `SigninLogs.ResultType` stay strings even
when the values look numeric. Needs Python 3.8+ and nothing else.
