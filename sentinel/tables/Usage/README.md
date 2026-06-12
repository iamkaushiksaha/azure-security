# Usage

> **Category:** Azure Monitor (LogManagement) — Log Analytics workspace ingestion/usage metering
> **Connector / source:** Emitted automatically by the **Log Analytics workspace** itself. No data connector or agent fills it — the platform writes one metering record per (table, solution) per **one-hour aggregation window** describing how much data that table ingested. Present in every workspace.
> **Table plan:** Analytics (default). The reference flags **Basic log: No** and **Ingestion-time DCR support: No** — `Usage` is a platform-generated billing/metering table and cannot itself be transformed or moved to Basic/Auxiliary.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/usage

## What this table is
Each row is a **per-table, per-hour ingestion meter** for one Log Analytics workspace: "in this one-hour window, table `DataType` (under `Solution`) ingested `Quantity` `QuantityUnit` (MBytes), and it `IsBillable` or not." It is written by the platform, not by an agent, so it exists in every workspace from day one. The metering window is bounded by `StartTime`/`EndTime` (a 1-hour slice) and `StartTime` equals `TimeGenerated`. It is the canonical source for **cost/chargeback reporting, capacity and cap planning, and data-coverage assurance** — and operationally it is the fastest way to spot an **ingestion anomaly**: a table that suddenly spikes (e.g. a burst of `SecurityEvent`/`StorageBlobLogs` during an incident) or one that suddenly **drops to zero** (a log source silently stopped — possible misconfiguration or deliberate logging tamper). It carries **no per-event security detail** (no users, IPs, hosts), so it supports detection only at the *meta* level of "is our telemetry healthy and are volumes normal."

## Schema
Full column list, validated against the Microsoft Learn reference. Types are KQL/Log Analytics types.

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | Date and time the record was created (same value as `StartTime`). |
| StartTime | datetime | Start time of the 1-hour aggregation window (same as `TimeGenerated`). |
| EndTime | datetime | End time of the 1-hour aggregation window. |
| DataType | string | **The table that usage is being reported about** (e.g. `SecurityEvent`, `SigninLogs`, `StorageBlobLogs`). This is the field you group by for per-table volume. |
| Solution | string | Solution the usage is reported under (e.g. `Security`, `LogManagement`, `Storage`). A table rolls up to a solution for billing. |
| Quantity | real | **Size of the ingested data, in MBytes.** This is the real metered amount. |
| QuantityUnit | string | Unit of `Quantity` — value is always `MBytes`. |
| IsBillable | bool | Whether this data record is billed (`true`/`false`). |
| Computer | string | **Deprecated** — effectively always empty; `Usage` is a workspace-level meter, not a per-host record. |
| ResourceUri | string | URI of the **workspace** the metering is for. Same value for every record in this table within a workspace. |
| MeterId | string | GUID of the billing meter used for this record. |
| Plan | string | Plan of the metered table at the time of ingestion (`Analytics`, `Basic`, or `Auxiliary`). |
| SourceSystem | string | Type of agent the event was collected by; for platform metering this is `Azure`. |
| Type | string | The name of the table (`Usage`). |

> **Total: 23 columns.** The 14 above are the operationally meaningful ones. The remaining 9 are **deprecated counters/identifiers and the standard billing columns** and should not be used in new queries: `AvgLatencyInSeconds` (real), `BatchesCapped` (long), `BatchesOutsideSla` (long), `BatchesWithinSla` (long), `TotalBatches` (long), `LinkedMeterId` (string), `LinkedResourceUri` (string), `Computer` (string, listed above), plus the system columns `_BilledSize` (real), `_IsBillable` (string — note the leading underscore; the boolean to use is `IsBillable`). No column was invented; there are no dynamic/nested columns in this table.

## Key columns for detection & hunting
- **Identity:** **n/a** — there is no user/actor column. `Usage` is volume metering; pivot to the metered table (`DataType`) and query *it* for identities.
- **Host / device:** **n/a** — `Computer` is deprecated and empty. This is a workspace-level (not host-level) meter.
- **Network:** **n/a** — no IP/port columns.
- **Outcome / result:** No success/failure column. The closest analytic signals are `Quantity` (the metered volume) and `IsBillable` (bool) — a table dropping to `Quantity == 0` is the "outcome" you hunt for.
- **Timestamps:** `TimeGenerated` = `StartTime` (window start) and `EndTime` (window end). Always a 1-hour `[StartTime, EndTime)` slice; use `StartTime`/`TimeGenerated` for time-series bucketing.
- **Join keys (to other tables):** `DataType` is the bridge — its value **is the name of another table in this workspace** (`SecurityEvent`, `SigninLogs`, `DnsEvents`, `StorageBlobLogs`, `AzureActivity`, `Syslog`, …), so `Usage` tells you *which table* to go investigate and over *what hour*. `ResourceUri` ties every row to the workspace. There are no event-level keys (no UPN/IP/host).

## ⚠️ Schema gotchas
- **`DataType` is the metered table's name, NOT `Type`.** `Type` is always literally `"Usage"`; `DataType` holds `"SecurityEvent"`, `"StorageBlobLogs"`, etc. Group by `DataType` for per-table volume — grouping by `Type` collapses everything into one bucket.
- **Two billable flags, different types.** Use the boolean **`IsBillable`** (`bool`). The lookalike **`_IsBillable`** is a *string* (`"true"`/`"false"`) and a deprecated/system column — don't mix them in a `where`/`summarize`.
- **`Quantity` is always MBytes.** `QuantityUnit` is informational ("always MBytes"); to report GB you must divide by 1024 yourself. Don't assume bytes.
- **`Computer` is deprecated and empty** — never filter or group by it. `Usage` is not a per-host table; the only resource scope is `ResourceUri` (the workspace).
- **Many columns are deprecated.** `AvgLatencyInSeconds`, `TotalBatches`, `Batches*`, `LinkedMeterId`, `LinkedResourceUri` are legacy and typically null/zero — they are not reliable SLA or latency signals. Build dashboards on `DataType` + `Quantity` + `StartTime` (+ `Solution`, `IsBillable`).
- **`Usage` measures volume, not events.** A volume spike is a *lead*, not evidence; always confirm by querying the metered table (`DataType`) for the same `[StartTime, EndTime)` window.

## 🧪 Sample data
[`Usage_sample.csv`](Usage_sample.csv) — 37 rows. Hourly ingestion meters across the morning of **2026-06-10** (the **Operation Quiet Ledger** incident day) for the workspace's key tables, showing a clear ingestion **spike inside the incident window (08:00–12:00)** and one source that **goes silent**: `SecurityEvent` rises from a ~530 MB/hr baseline to **3187 MB** at 09:00 (process/4688 storm), `StorageBlobLogs` jumps to **5821 MB** at 10:00 (blob exfil hour), `DnsEvents` to ~890 MB at 09:00 (C2 lookups), `SigninLogs` and `AzureActivity` rise during the Azure pivot — while `Syslog` collapses from ~390 MB to **0 MB at 11:00** (Linux foothold host's logging stops). `AzureDiagnostics` and `Heartbeat` stay flat as a benign baseline so anomalies stand out.
The sample uses this curated subset of **real** columns: `TimeGenerated`, `StartTime`, `EndTime`, `DataType`, `Solution`, `Quantity`, `QuantityUnit`, `IsBillable`, `Computer`, `ResourceUri`, `MeterId`, `SourceSystem`. This table **cannot carry the per-event attack narrative** — it is the **operational telemetry-health / cost view** of the cross-table scenario: the same incident seen as "which tables surged, and which fell silent," over the 08:00–12:00 window.

## 🎯 Threat-hunting hypotheses (single-table)
These run against `Usage` at the *meta* level — they surface tables to go investigate, not events themselves.

### H1 · Ingestion spike — a table's hourly volume jumps far above its own baseline — [T1078](https://attack.mitre.org/techniques/T1078/)
**Hypothesis:** A table whose hourly `Quantity` rises well above its recent per-table baseline can indicate incident activity generating a telemetry surge (process-creation storms, mass blob access, DNS C2 floods). Compute each `DataType`'s baseline from its quieter hours and flag windows that exceed it.
```kusto
Usage
| where QuantityUnit == "MBytes"
| summarize Baseline = percentile(Quantity, 50), Peak = max(Quantity),
            PeakHour = arg_max(Quantity, StartTime)
        by DataType
| extend SpikeRatio = round(Peak / Baseline, 1)
| where SpikeRatio >= 2.0 and Peak > 200
| sort by SpikeRatio desc
```
**Triage:** True positive = an *unexpected* surge whose peak hour lines up with the incident window — here `StorageBlobLogs` (~15x, peak 10:00) and `SecurityEvent` (~6x, peak 09:00); confirm by querying that `DataType` for `[StartTime, EndTime)`. Benign = a scheduled batch, planned onboarding of a new source, or a backfill/replay that explains the rise.

### H2 · Source went silent — a table that was reporting suddenly drops to zero — [T1562.008](https://attack.mitre.org/techniques/T1562/008/)
**Hypothesis:** A table that was steadily ingesting and then reports `Quantity == 0` (or stops appearing) for an hour may mean a log source was disabled — agent stopped, diagnostic setting removed, or audit logging deliberately turned off to blind the SOC (impair defenses / disable cloud logs).
```kusto
Usage
| where QuantityUnit == "MBytes"
| summarize HoursReporting = count(),
            ActiveMB = sumif(Quantity, Quantity > 0),
            ZeroHours = countif(Quantity == 0),
            LastNonZero = maxif(StartTime, Quantity > 0),
            LastSeen    = max(StartTime)
        by DataType
| where ActiveMB > 0 and ZeroHours > 0
| extend SilentSince = LastNonZero
| project DataType, ActiveMB, ZeroHours, SilentSince, LastSeen
| sort by SilentSince asc
```
**Triage:** True positive = a previously-busy security source (here `Syslog`, active then `0` at 11:00) going quiet with no change ticket — cross-check `Heartbeat` for the host(s) and the diagnostic-setting/agent config. Benign = decommissioned source, a maintenance window, or a genuinely idle low-volume table.

### H3 · Cost / coverage assurance — top tables and the billable share by solution — [T1530](https://attack.mitre.org/techniques/T1530/)
**Hypothesis:** Day-level ranking of ingested volume by `DataType` and `Solution` answers two SOC questions at once: *what is driving cost* and *is every expected security source still present* (a source missing from the ranking = a coverage gap). A sudden newcomer at the top, or an expected source absent, both warrant a look.
```kusto
Usage
| where QuantityUnit == "MBytes"
| summarize TotalMB = sum(Quantity),
            BillableMB = sumif(Quantity, IsBillable == true),
            Hours = dcount(StartTime)
        by DataType, Solution
| extend TotalGB = round(TotalMB / 1024, 2),
         BillablePct = round(100.0 * BillableMB / TotalMB, 1)
| sort by TotalMB desc
```
**Triage:** True positive (worth attention) = an unexpected table dominating volume, or a security-critical `DataType` (e.g. `SecurityEvent`, `SigninLogs`) **absent** from the list = a coverage gap. Benign = the normal mix where high-volume diagnostic/security tables lead and billable share matches the workspace's commitment tier.

## 🔗 Correlates with
`Usage` is a **meta/operational** table — its `DataType` value names the table you pivot *into*, scoped by the `[StartTime, EndTime)` hour:
- **SecurityEvent** — when `DataType == "SecurityEvent"` spikes, query `SecurityEvent` for that hour for the 4688/process storm on `FIN-WS-07`/`DC01` driving the surge.
- **StorageBlobLogs** — a `StorageBlobLogs` spike (peak 10:00) points to the **blob-exfil** hour; pivot to the storage logs for `stcontosofin` to see the reads.
- **DnsEvents** — a `DnsEvents` surge maps to the **C2 lookup** burst; pivot to `DnsEvents` for the `badupdate-cdn.com` queries.
- **Syslog / Heartbeat** — when `DataType == "Syslog"` drops to zero, correlate with **`Heartbeat`** on the Linux host (`WEB-APP-01`) to tell "agent/host down" from "logging disabled," and check `Syslog` directly for the last events before silence.

## 📚 References
- [Usage — Azure Monitor Logs table reference](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/usage)
- [Analyze usage in a Log Analytics workspace](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/analyze-usage)
- [Sample queries for the Usage table](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/queries/usage)
