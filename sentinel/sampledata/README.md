# Sample data (Lab 02 — simplified teaching CSVs)

These are **deliberately simplified, few-column CSVs** used by the ADX setup labs
([ADX setup](../labs/adx-setup.md) · [ADX table scripts](../labs/adx-table-scripts.md))
to teach table creation and ingestion. The `.create table` scripts in those labs are matched to
these reduced schemas.

| CSV | Used by | Notes |
|---|---|---|
| `SigninLogs_sample.csv` | ADX table scripts | 11-column teaching subset |
| `SigninLogs_sample_important_columns_110rows.csv` | ADX setup | 110 rows — volume for ingestion practice |
| `AuditLogs_sample.csv` · `SecurityEvent_sample.csv` · `AzureActivity_sample.csv` · `OfficeActivity_sample.csv` | ADX table scripts | reduced teaching schemas |

> [!IMPORTANT]
> **For schema-true data, use the [Sentinel Table Library](../tables/README.md) instead.**
> It has every column validated against Microsoft Learn, gotchas, MITRE-mapped hunts, and a
> correlated [attack scenario](../tables/scenarios/operation-quiet-ledger/README.md) — 27 tables.
> To ingest any of those into ADX with a correct auto-generated schema, use the skill's generator:
>
> ```bash
> python3 .claude/skills/azure-sentinel-hunter/scripts/csv_to_kql.py \
>     sentinel/tables/SigninLogs/SigninLogs_sample.csv --mode adx
> ```
>
> The simplified CSVs here remain only because the Lab 02 walkthroughs are written against their
> reduced schemas. New work should target the table library.
