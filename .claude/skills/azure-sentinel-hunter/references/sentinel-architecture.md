# Sentinel architecture & cost — the context that shapes queries

You don't need to be an architect to hunt, but these facts change how you write queries, what you
can alert on, and what a query costs.

## Workspace & data model
- Sentinel is a solution **on top of a Log Analytics workspace**; tables live there and are queried
  with KQL. Defender XDR "advanced hunting" queries the same KQL over `Device*`, `Email*`, identity
  tables — skills transfer directly.
- **`TimeGenerated`** is the universal time column — filter on it in every query.
- Tables come from **data connectors** (Entra, Defender, Office 365, AMA for Windows/Syslog, ARM
  activity, diagnostic settings). **No connector → empty table** → queries return nothing. This is
  why the [sample-data library](../../../../sentinel/tables/README.md) exists: to develop against an
  empty estate.

## Table plans — they limit what you can do
| Plan | Retention/behavior | Query/alert limits |
|---|---|---|
| **Analytics** | Full interactive + analytics; default | All operators; scheduled rules; full KQL |
| **Basic / Auxiliary** | Cheap ingest, long cheap retention, lake-style | **Restricted** operators, limited/one-table query, restricted alerting, per-query retrieval cost |

Several security tables can sit on **Basic** (e.g. `DeviceProcessEvents`, `DeviceNetworkEvents`,
device tables, some Defender tables). Before building heavy `join`/aggregation or a scheduled rule
over long ranges, **check the plan** — a Basic table may not support your query or alerting. The
table-library docs flag the plan per table.

## Retention
- **Interactive retention** (queryable now) vs **long-term/archive** (cheaper, restore or
  search-job to query). Default interactive is workspace-configurable (commonly 90 days; up to
  years). Archived data isn't in normal queries until restored.
- Hunts over old data may need a **search job** or **restore** — they won't appear in a plain query
  past the interactive window.

## Ingestion-time control (DCRs & transformations)
- **Data Collection Rules (DCRs)** govern what's collected (e.g. which Windows Event IDs, which
  Syslog facilities) and can **transform/filter/enrich at ingestion** (drop noise, redact PII, route
  to Basic, add columns). If a column you expect is empty, a DCR filter may be the cause.
- Ingestion-time transforms reduce cost but can also **remove fields your detection needs** — verify
  against the *actual* workspace, not just the MS Learn schema.

## Cost awareness (it changes query design)
- Billing is by **GB ingested** (+ retention/restore/search-job). The expensive operations for a
  hunter are **archive restores** and **search jobs**, not interactive queries.
- Keep noisy-but-low-value sources on Basic; keep detection-critical sources on Analytics.
- This is why **filter-early** matters beyond speed — and why over-broad rules that scan wide ranges
  are both slow and a cost signal.

## RBAC & operational notes
- Roles: **Sentinel Reader / Responder / Contributor**, plus Log Analytics roles. *Saving a
  function* or deploying rules needs write access — Readers can still query. (The KQL course's
  zero-permission `let datatable()` pattern exists for exactly this.)
- **Detections as code:** manage analytic rules/hunting queries as YAML in version control and
  deploy via the Sentinel **repositories / CI-CD** connection for review and auditability.
- **Watchlists** hold tunable reference data (allow-lists, asset inventories, VIP users) queried via
  `_GetWatchlist()` — prefer them over hard-coded lists so tuning doesn't require editing rules.

References: [Sentinel overview](https://learn.microsoft.com/en-us/azure/sentinel/overview) ·
[Table plans](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/data-platform-logs#table-plans) ·
[Manage retention](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/data-retention-configure) ·
[DCR transformations](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/data-collection-transformations) ·
[Sentinel costs](https://learn.microsoft.com/en-us/azure/sentinel/billing) ·
[Roles & permissions](https://learn.microsoft.com/en-us/azure/sentinel/roles)
