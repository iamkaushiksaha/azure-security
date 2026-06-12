# Stage 03 · Advanced KQL — Production techniques

> **Audience:** SOC analysts advancing to threat hunting, detection engineers, architects.
> **Tables:** this stage uses the **real** Sentinel tables (`SigninLogs`, `AuditLogs`, `SecurityEvent`, …). They return data only where the relevant connector is ingesting.
> **Empty workspace? Run these anyway.** The [Sentinel Table Library](../../tables/README.md) ships schema-true sample logs for these exact tables — ingest them into an [ADX free cluster](../00-setup/README.md#method-2--azure-data-explorer-free-cluster--csv) (or paste a `let datatable()` from its `csv_to_kql.py`) and the real-table queries below run as-is, returning the [Operation Quiet Ledger](../../tables/scenarios/operation-quiet-ledger/README.md) attack data.

> ⚠️ **Real-table reminder:** in `SigninLogs`, `ResultType` is a **string** — use `ResultType != "0"`, not `!= 0`. (It's an int only in the demo set.) [SigninLogs reference](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/signinlogs)

---

## 1. Advanced aggregation

Beyond `count()` and `sum()`, KQL has a rich aggregation set: conditional counts (`countif`), approximate distinct counts (`dcount`), percentiles (`percentile`/`percentiles`), and whole-record retrieval (`arg_max`/`arg_min`). Combine several in one `summarize`.

```kusto
SigninLogs
| where TimeGenerated > ago(7d)
| summarize TotalLogins = count(),
            FailedLogins = countif(ResultType != "0")
        by UserPrincipalName
| sort by FailedLogins desc
```

Latest record per group with `arg_max` — the `*` (or a list of columns) returns the rest of the winning row:

```kusto
SigninLogs
| where TimeGenerated > ago(7d)
| summarize arg_max(TimeGenerated, IPAddress, AppDisplayName) by UserPrincipalName
```

> Always include a time filter (`TimeGenerated > ago(7d)`) to bound the scan.
> Reference: [Aggregation functions](https://learn.microsoft.com/en-us/kusto/query/aggregation-functions?view=microsoft-sentinel) · [arg_max()](https://learn.microsoft.com/en-us/kusto/query/arg-max-aggregation-function?view=microsoft-sentinel)

## 2. Time series with `bin()`

```kusto
SigninLogs
| where TimeGenerated > ago(30d)
| summarize LoginCount = count() by bin(TimeGenerated, 1d)
| render timechart
```

`bin()` is a floor operation on time (or numbers). Pick a size that fits the span — daily for long ranges, hourly for recent detail. Reference: [bin()](https://learn.microsoft.com/en-us/kusto/query/bin-function?view=microsoft-sentinel)

## 3. Join types and when to use them

| Flavour | Returns | Use for |
|---|---|---|
| `inner` | only rows matching on both sides | correlated events present in both datasets |
| `leftouter` | all left rows + right data where matched | **enrichment** (e.g. alerts + threat intel) |
| `rightouter` | all right rows + left where matched | rare; reference set on the right |
| `leftanti` / `anti` | left rows with **no** match on the right | "find what's missing" (logon with no logoff) |
| `lookup` | left extended with small right table, no key duplication | enriching large data with a small mapping |

Reference: [join operator](https://learn.microsoft.com/en-us/kusto/query/join-operator?view=microsoft-sentinel) · [lookup operator](https://learn.microsoft.com/en-us/kusto/query/lookup-operator?view=microsoft-sentinel)

**Example — session duration** by correlating logon (4624) and logoff (4634) on stable keys, with the same time filter on both sides:

```kusto
SecurityEvent
| where TimeGenerated > ago(1d) and EventID == 4624
| project Computer, Account, LogonTime = TimeGenerated
| join kind=inner (
    SecurityEvent
    | where TimeGenerated > ago(1d) and EventID == 4634
    | project Computer, Account, LogoffTime = TimeGenerated
) on Computer, Account
| extend SessionDuration = LogoffTime - LogonTime
| project Account, Computer, LogonTime, LogoffTime, SessionDuration
```

> **Best practice:** time-filter **both** sides; join on stable keys (UPN, Computer, IP, CorrelationId); normalise case with `tolower()` if needed. To find logons *without* a logoff, swap `kind=inner` for `kind=leftanti`.
> Reference: [Optimize log queries](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/query-optimization)

## 4. Parsing & extracting fields

Logs often hide data inside strings or dynamic (JSON) columns.

### `parse` — split structured text into columns

> 🧩 **Illustrative pattern — not runnable as-is.** `MyTable`/`Message` are placeholders for *whatever table holds a delimited string column*. Swap them for a real one (e.g. `Syslog`/`SyslogMessage` — see the [Syslog sample](../../tables/Syslog/README.md), whose hunts parse exactly this way).

```kusto
// Message like: "SrcIP=10.0.0.1; DestIP=10.0.0.5; Action=Allow"
MyTable
| parse Message with "SrcIP=" SrcIp "; DestIP=" DestIp "; Action=" Action
| project SrcIp, DestIp, Action
```

Use `parse kind=regex` for regex patterns, or `parse-where` to keep only rows that matched. Reference: [parse operator](https://learn.microsoft.com/en-us/kusto/query/parse-operator?view=microsoft-sentinel)

### `extract()` — one regex capture, inline

```kusto
// Pull the domain after the @ in a UPN
SigninLogs
| extend Domain = extract(@"@(.+)$", 1, UserPrincipalName)
```

The third arg is the source string; `1` is the capture group. No match → null. Reference: [extract()](https://learn.microsoft.com/en-us/kusto/query/extract-function?view=microsoft-sentinel)

### Dynamic / JSON columns — dot notation

Many Sentinel tables have `dynamic` columns. **`AuditLogs.InitiatedBy` is already dynamic**, so you drill straight in with dot notation (no `parse_json` needed) and cast the leaf with `tostring()`:

```kusto
AuditLogs
| where TimeGenerated > ago(7d)
| extend Initiator   = tostring(InitiatedBy.user.userPrincipalName)
| extend TargetObject = tostring(TargetResources[0].displayName)
| project TimeGenerated, Initiator, OperationName, Result, TargetObject
```

> If a column is a JSON **string** (not already dynamic), wrap it once with `parse_json()` / `todynamic()` before indexing. Reference: [parse_json()](https://learn.microsoft.com/en-us/kusto/query/parse-json-function?view=microsoft-sentinel) · [dynamic type](https://learn.microsoft.com/en-us/kusto/query/scalar-data-types/dynamic?view=microsoft-sentinel)

### `mv-expand` — one array element per row

`TargetResources` is an array. Expand it to aggregate per target:

```kusto
AuditLogs
| where TimeGenerated > ago(7d)
| mv-expand TargetResource = TargetResources
| extend ResourceName = tostring(TargetResource.displayName)
| summarize Changes = count() by ResourceName
| sort by Changes desc
```

Filter **before** expanding to limit row blow-up. Reference: [mv-expand operator](https://learn.microsoft.com/en-us/kusto/query/mv-expand-operator?view=microsoft-sentinel)

## 5. Modular queries with `let`

Break complex logic into named parts — clearer and easier to tune.

```kusto
let failedCountByUser =
    SigninLogs
    | where TimeGenerated > ago(1d) and ResultType != "0"
    | summarize FailedCount = count() by UserPrincipalName;
failedCountByUser
| where FailedCount > 5
```

**Scope time filters inside each subquery** so both sides of a union/join are bounded early:

```kusto
let MinTime = ago(1d);
Heartbeat
| where TimeGenerated > MinTime
| summarize arg_min(TimeGenerated, *) by Computer
| union (
    Perf
    | where TimeGenerated > MinTime
    | summarize arg_min(TimeGenerated, *) by Computer
)
```

`let` can also hold a scalar via `toscalar()` for percentage calculations, thresholds, etc. If a heavy subquery is reused many times, consider `materialize()`.
Reference: [let statement](https://learn.microsoft.com/en-us/kusto/query/let-statement?view=microsoft-sentinel)

## 6. ASIM — normalized, source-agnostic queries

The **Advanced Security Information Model (ASIM)** gives Sentinel a standard schema per activity type, exposed through **unifying parsers** named **`_Im_<Schema>`** (note the **leading underscore**). One ASIM query covers every source that has a parser for that schema.

> ✅ **Correctness fixes vs. common write-ups:**
> - The parser name needs the leading underscore: `_Im_Dns`, `_Im_Authentication` — not `Im_Dns`.
> - **Filtering parameters in the call are lowercase** (`starttime=`, `responsecodename=`, `eventresult=`), even though the **output** fields are PascalCase (`ResponseCodeName`, `SrcIpAddr`).
> Source: [Use ASIM parsers](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers)

> [!NOTE]
> **ASIM parsers live in Microsoft Sentinel**, not in plain Log Analytics and **not in an ADX free cluster**. If `_Im_Authentication` returns *"unknown function"*, you're not in a Sentinel-enabled workspace — that's expected. Study the pattern here and run the raw-table equivalents (e.g. the `SigninLogs` failed-auth query in §1) against the [table library samples](../../tables/README.md) instead.

```kusto
// Normalized DNS — filtering params (lowercase) run BEFORE parsing for speed
_Im_Dns(starttime=ago(1d), responsecodename='NXDOMAIN')
| summarize count() by SrcIpAddr, bin(TimeGenerated, 15m)
```

```kusto
// Failed authentications across every identity source that has a parser
_Im_Authentication(starttime=ago(1h), eventresult='Failure')
| summarize Failures = count() by TargetUserId
| sort by Failures desc
```

**Why prefer ASIM:** portable across sources and environments, future-proof (new sources with a parser are picked up automatically), and broad detection coverage from a single query. Always pass at least `starttime=` for performance. Use raw tables only for one-off exploration or where no parser exists.

## 7. Shaping output for visualizations

The `render` engine uses the **first column's type** to choose the X-axis, and numeric columns as values. Shape the result with `project`/`summarize` so it has exactly what the chart needs.

```kusto
// Timechart: datetime first, numeric next, one string col → separate series
SigninLogs
| where TimeGenerated > ago(24h)
| summarize Count = count() by bin(TimeGenerated, 1h), ResultType
| render timechart
```

```kusto
// Columnchart: category first, numeric second
SecurityAlert
| summarize AlertCount = count() by AlertSeverity
| project Severity = AlertSeverity, AlertCount
| render columnchart
```

- **Timechart:** datetime, then numeric(s), then at most one string (= series). Extra strings are ignored.
- **Bar/column/pie:** category first, numeric value second.
- Use friendly column names via `project`, or set titles with `render ... with (title="...", ytitle="...")`.

Reference: [render operator](https://learn.microsoft.com/en-us/kusto/query/render-operator?view=microsoft-sentinel) · [Time chart](https://learn.microsoft.com/en-us/kusto/query/visualization-timechart?view=microsoft-sentinel)

## 8. Advanced operators — know they exist

| Operator / function | What it does |
|---|---|
| `make-series` | Builds a complete, gap-filled array of values along a time axis — for anomaly detection / forecasting. [docs](https://learn.microsoft.com/en-us/kusto/query/make-series-operator?view=microsoft-sentinel) |
| `series_decompose_anomalies()` | Flags statistically anomalous points in a series (trend/seasonality/residual). [docs](https://learn.microsoft.com/en-us/kusto/query/series-decompose-anomalies-function?view=microsoft-sentinel) |
| `bag_pack()` / `pack()` | Builds a dynamic property bag (JSON object) from columns. [docs](https://learn.microsoft.com/en-us/kusto/query/pack-function?view=microsoft-sentinel) |
| `evaluate bag_unpack()` | Expands a dynamic property bag into individual columns. [docs](https://learn.microsoft.com/en-us/kusto/query/bag-unpack-plugin?view=microsoft-sentinel) |
| `mv-apply` | Runs a sub-query per expanded array element. [docs](https://learn.microsoft.com/en-us/kusto/query/mv-apply-operator?view=microsoft-sentinel) |

These power trend analysis, anomaly hunting, and nested-data flattening. Reach for them when filtering and counting aren't enough.

---

## 🧪 Exercises (adapt to `DemoIdentityLogs` if you have no real data)

1. Per user in `SigninLogs`, compute total logins and the **failure rate** as a percentage.
2. From `AuditLogs`, extract the initiator UPN from `InitiatedBy` and count operations per initiator.
3. Use `leftanti` to find users who appear in `SigninLogs` but **never** in `AuditLogs`.
4. Rewrite a failed-auth query using `_Im_Authentication` with proper lowercase filtering parameters.

<details>
<summary><b>Answers</b></summary>

```kusto
// 1
SigninLogs
| where TimeGenerated > ago(7d)
| summarize Total = count(), Failed = countif(ResultType != "0") by UserPrincipalName
| extend FailureRatePct = round(100.0 * Failed / Total, 1)
| sort by FailureRatePct desc
```
```kusto
// 2
AuditLogs
| where TimeGenerated > ago(7d)
| extend Initiator = tostring(InitiatedBy.user.userPrincipalName)
| where isnotempty(Initiator)
| summarize Operations = count() by Initiator
| sort by Operations desc
```
```kusto
// 3
SigninLogs
| where TimeGenerated > ago(7d)
| distinct UserPrincipalName
| join kind=leftanti (
    AuditLogs
    | where TimeGenerated > ago(7d)
    | extend UserPrincipalName = tostring(InitiatedBy.user.userPrincipalName)
    | distinct UserPrincipalName
) on UserPrincipalName
```
```kusto
// 4
_Im_Authentication(starttime=ago(24h), eventresult='Failure')
| summarize Failures = count() by TargetUserId, SrcIpAddr
| sort by Failures desc
```
</details>

---

## ✅ You'll know you've completed Stage 03 when you can

- [ ] drill into a dynamic/JSON column (`tostring(InitiatedBy.user.userPrincipalName)`) and `mv-expand` an array;
- [ ] pick the right `join` flavour (`inner`/`leftouter`/`leftanti`/`lookup`) for the question;
- [ ] modularise a query with `let` and scope the time filter inside each subquery;
- [ ] write a normalised `_Im_*` ASIM query with lowercase call params — and know it needs a Sentinel workspace.

**Next:** [Stage 04 · Threat Hunting](../04-hunting/README.md) — MITRE-mapped hunts across identity and endpoint.
