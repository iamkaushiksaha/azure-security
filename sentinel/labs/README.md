# Azure Data Explorer labs

Practise Sentinel-style KQL on an Azure Data Explorer (ADX) free cluster, with no Sentinel workspace and no Azure
subscription. The [KQL reference course](../kql/README.md) covers the quickest route in its Stage 00 (Method 2);
these labs go further and load several tables, so you can practise joins.

| Lab | What you do |
|---|---|
| [ADX setup](adx-setup.md) | Create a free cluster, create a `SigninLogs` table and load sample sign-ins |
| [ADX table scripts](adx-table-scripts.md) | Create `AuditLogs`, `AzureActivity`, `OfficeActivity` and `SecurityEvent` and load their samples |

The CSVs are in [`../sampledata/`](../sampledata/README.md): small, synthetic teaching subsets with fewer columns
than the real tables. For full-schema samples of 27 tables, use the [table library](../tables/README.md).

ADX speaks the same query language, but Sentinel-only features (ASIM parsers, watchlists, the workspace's own
tables and functions) aren't there.
