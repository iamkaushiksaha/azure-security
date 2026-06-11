# Microsoft Reference Links

Tier-1 (Microsoft Learn) sources used throughout this lab, grouped by topic. Verify any volatile claim here before relying on it.

## Getting started / practice environments
- Free Azure Data Explorer cluster: https://learn.microsoft.com/en-us/azure/data-explorer/start-for-free
- Create the free cluster (web UI): https://learn.microsoft.com/en-us/azure/data-explorer/start-for-free-web-ui
- Create the free cluster (direct): https://aka.ms/kustofree
- Get data from a local file (CSV ingestion): https://learn.microsoft.com/en-us/azure/data-explorer/get-data-file
- ADX web UI: https://dataexplorer.azure.com/home

## KQL language
- KQL overview: https://learn.microsoft.com/en-us/kusto/query/?view=microsoft-sentinel
- Learn common operators (tutorial): https://learn.microsoft.com/en-us/kusto/query/tutorials/learn-common-operators?view=microsoft-sentinel
- KQL learning resources: https://learn.microsoft.com/en-us/azure/data-explorer/kql-learning-resources
- datatable operator: https://learn.microsoft.com/en-us/kusto/query/datatable-operator?view=microsoft-sentinel
- let statement: https://learn.microsoft.com/en-us/kusto/query/let-statement?view=microsoft-sentinel
- where / string operators: https://learn.microsoft.com/en-us/kusto/query/datatypes-string-operators?view=microsoft-sentinel
- summarize operator: https://learn.microsoft.com/en-us/kusto/query/summarize-operator?view=microsoft-sentinel
- Aggregation functions: https://learn.microsoft.com/en-us/kusto/query/aggregation-functions?view=microsoft-sentinel
- arg_max(): https://learn.microsoft.com/en-us/kusto/query/arg-max-aggregation-function?view=microsoft-sentinel
- bin(): https://learn.microsoft.com/en-us/kusto/query/bin-function?view=microsoft-sentinel
- join operator: https://learn.microsoft.com/en-us/kusto/query/join-operator?view=microsoft-sentinel
- lookup operator: https://learn.microsoft.com/en-us/kusto/query/lookup-operator?view=microsoft-sentinel
- union operator: https://learn.microsoft.com/en-us/kusto/query/union-operator?view=microsoft-sentinel
- parse operator: https://learn.microsoft.com/en-us/kusto/query/parse-operator?view=microsoft-sentinel
- extract(): https://learn.microsoft.com/en-us/kusto/query/extract-function?view=microsoft-sentinel
- parse_json(): https://learn.microsoft.com/en-us/kusto/query/parse-json-function?view=microsoft-sentinel
- mv-expand operator: https://learn.microsoft.com/en-us/kusto/query/mv-expand-operator?view=microsoft-sentinel
- dynamic type: https://learn.microsoft.com/en-us/kusto/query/scalar-data-types/dynamic?view=microsoft-sentinel
- render operator: https://learn.microsoft.com/en-us/kusto/query/render-operator?view=microsoft-sentinel
- make-series operator: https://learn.microsoft.com/en-us/kusto/query/make-series-operator?view=microsoft-sentinel
- series_decompose_anomalies(): https://learn.microsoft.com/en-us/kusto/query/series-decompose-anomalies-function?view=microsoft-sentinel
- bag_unpack plugin: https://learn.microsoft.com/en-us/kusto/query/bag-unpack-plugin?view=microsoft-sentinel
- Optimize log queries: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/query-optimization

## Table schema references (validate columns here)
- SigninLogs: https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/signinlogs
- AuditLogs: https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/auditlogs
- DeviceProcessEvents: https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/deviceprocessevents
- DeviceNetworkEvents: https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/devicenetworkevents
- CommonSecurityLog: https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/commonsecuritylog
- Logs index (all tables): https://learn.microsoft.com/en-us/azure/azure-monitor/reference/logs-index
- Table plans (Basic vs Analytics): https://learn.microsoft.com/en-us/azure/azure-monitor/logs/logs-table-plans?tabs=portal-1
- Save a query as a function: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/functions

## Sentinel / Defender / ASIM / Hunting
- ASIM parsers (normalization): https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers
- Hunt for threats in Sentinel: https://learn.microsoft.com/en-us/azure/sentinel/hunting
- Advanced hunting in Defender XDR: https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-overview
- MITRE ATT&CK: https://attack.mitre.org/

> **Note on doc views:** Kusto query pages accept both `view=microsoft-sentinel` and `view=microsoft-fabric`; this lab standardises on `microsoft-sentinel`. Table-reference pages occasionally publish under `en-in`; swap the locale if a link 404s.
