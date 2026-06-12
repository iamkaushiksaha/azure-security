# KQL best practices — authoring & debugging

Opinionated rules for writing Kusto that is **correct, fast, and readable**, in that order. Assumes
you've already confirmed the schema (see [schema-and-asim.md](schema-and-asim.md)).

## Correctness first

- **Type-match every predicate.** The single most common silent bug. Know the type before you
  compare:
  - `SigninLogs.ResultType` → **string** → `where ResultType == "0"` (success). `!= 0` (int) is a bug.
  - `SecurityEvent.EventID` → **int** → `where EventID == 4625`.
  - `AuditLogs.Result` → **string** (`success`/`failure`); `ResultType` there is also a string.
  - `StorageBlobLogs.StatusCode` → **string** (`"200"`).
  - dynamic JSON: `AKSAudit.ResponseStatus`, `AzureActivity.Authorization_d`, `SigninLogs.Status`,
    `AuditLogs.InitiatedBy` — drill with dot/`[index]` and cast the leaf (`tostring`, `toint`).
- **Pull identity from the correct column** (it is *not* `UserPrincipalName` everywhere):

  | Table | Identity expression |
  |---|---|
  | `SigninLogs` | `UserPrincipalName` |
  | `AuditLogs` | `tostring(InitiatedBy.user.userPrincipalName)` |
  | `OfficeActivity` | `UserId` |
  | `AzureActivity` | `Caller` (UPN for users, **GUID** for service principals) |
  | `SecurityEvent` | `Account` / `TargetUserName` / `SubjectUserName` |
  | `CommonSecurityLog` | `SourceUserName` / `DestinationUserName` |
  | `AKSAudit` / `AKSAuditAdmin` | `tostring(User.username)` |
  | `StorageBlobLogs` | `RequesterUpn` / `RequesterObjectId` (**OAuth only** — empty for AccountKey/SAS) |
  | `Syslog` / `LinuxAuditLog` | parse from `SyslogMessage` / the `acct`/`auid` fields |

- **Empty ≠ matched.** `where Col == ""` and a missing column behave differently. Use
  `isempty()`/`isnotempty()`/`isnull()` deliberately.
- **Beware `join` defaults.** Default `join` is `innerunique` (deduplicates the left key) — usually
  *not* what you want for counting. Specify `kind=inner` explicitly when you mean a true inner join.

## Performance

Order operators so the engine scans as little as possible:

1. **`where TimeGenerated > ago(<window>)` first.** Always. Unbounded queries scan everything.
2. **Most selective filters next** — exact `==`/`in` before `has` before `contains`/`matches regex`.
3. **`has`/`has_any` over `contains`.** Token-indexed = fast. `contains`/`endswith`/`matches regex`
   are unindexed substring scans — only when you truly need them.
4. **Reduce columns early** with `project`/`project-away` before heavy `summarize`/`join`.
5. **Filter before `mv-expand`/`parse`/`extend`** — never expand an array and *then* filter.
6. **Join small-to-large:** put the smaller, pre-filtered set on the **left** of `join`; consider
   `hint.strategy=broadcast` for a tiny lookup against a huge table; use `lookup` for enrichment
   from a small dimension table (no key duplication).
7. **`summarize` cost:** `dcount()` is approximate-and-cheap; exact distinct (`count(distinct)`)
   does not exist — use `dcount()` or `make_set()`+`array_length()`. `arg_max(t, *)` carries the
   whole winning row; list specific columns instead of `*` on very wide tables.
8. **`materialize()`** a sub-result used multiple times in the same query (e.g. in a `union` of
   derivations) so it computes once.
9. **`take`/`limit` is unordered** — only for sampling, never for "top N" (use `top N by Col`).

## Readability & reuse

- **`let` for everything reused or named** — lookback windows, IOC lists, threshold scalars
  (`let threshold = toscalar(...)`), and sub-results. Self-documents intent.
- **One transformation per line**, piped top-to-bottom; read a query like a sentence.
- **Name computed columns** for the human/entity-mapping/chart that consumes them.
- **Comment the *why*,** not the *what* — especially a threshold's rationale or a known FP source.

## The operator toolkit (when to reach for what)

| Need | Operator/function |
|---|---|
| Filter rows | `where` (+ `isnotempty`, `in~`, `has_any`) |
| Add/derive columns | `extend`, `iff`, `case`, `coalesce` |
| Aggregate | `summarize count()/countif()/dcount()/make_set()/make_list()/arg_max()` |
| Time series | `summarize ... by bin(TimeGenerated, 1h)` → `render timechart` |
| Gap-filled series + anomalies | `make-series` → `series_decompose_anomalies()` |
| Stack sources | `union` (scope each leg's time filter) |
| Correlate | `join kind=inner\|leftouter\|leftanti\|...`, `lookup` |
| Find what's missing | `join kind=leftanti` (logon without logoff, user never in table B) |
| Split text | `parse`, `parse kind=regex`, `extract(regex, n, src)` |
| JSON | dot/`[i]` on dynamic; `parse_json()`/`todynamic()` for JSON-in-string first |
| Array → rows | `mv-expand`; per-element subquery → `mv-apply` |
| Property bag → columns | `evaluate bag_unpack()` |
| Enrich w/ external list | `externaldata`, watchlists (`_GetWatchlist()`), `ipv4_lookup` |

## Detection-flavored patterns

```kusto
// Failures-then-success (credential-attack success) — generic shape
let lookback = 1d;
let fails =
    SigninLogs
    | where TimeGenerated > ago(lookback) and ResultType != "0"
    | summarize Fails = count(), LastFail = max(TimeGenerated) by UserPrincipalName
    | where Fails >= 10;
SigninLogs
| where TimeGenerated > ago(lookback) and ResultType == "0"
| join kind=inner fails on UserPrincipalName
| where TimeGenerated > LastFail
| project SuccessTime = TimeGenerated, UserPrincipalName, IPAddress, Location, Fails
```

```kusto
// Rare-value / first-seen baseline (new ASN per user vs 14d history)
let hist = SigninLogs | where TimeGenerated between (ago(14d) .. ago(1d))
    | summarize Known = make_set(AutonomousSystemNumber) by UserPrincipalName;
SigninLogs
| where TimeGenerated > ago(1d) and ResultType == "0"
| join kind=leftouter hist on UserPrincipalName
| where not(set_has_element(Known, AutonomousSystemNumber))
```

```kusto
// Beaconing / regularity via time-delta stddev (low jitter = automated)
DnsEvents
| where TimeGenerated > ago(1d) and SubType == "LookupQuery"
| order by ClientIP, Name, TimeGenerated asc
| serialize delta = datetime_diff('second', TimeGenerated, prev(TimeGenerated))
| summarize Beacons = count(), JitterStdev = stdev(delta), AvgInterval = avg(delta)
        by ClientIP, Name
| where Beacons > 10 and JitterStdev < 30
```

## Common traps checklist
- String-vs-int `ResultType` (Signin) — `"0"` not `0`.
- Identity in a dynamic column (`AuditLogs.InitiatedBy`) — `tostring(...userPrincipalName)`.
- `CallerIpAddress` may include a `:port` (StorageBlobLogs) — `split(CallerIpAddress, ":")[0]`.
- `IPAddresses` (DnsEvents) is a comma-joined **string**, not an array.
- Default `join` is `innerunique` — set `kind=inner` when counting.
- `AzureActivity` emits Start+Success rows sharing `CorrelationId` — dedupe before counting ops.
- `take`/`limit` is not ordered — use `top ... by`.
- Source IP column name varies: `IPAddress` (Signin) vs `IpAddress` (SecurityEvent) vs `SourceIP`
  (CommonSecurityLog) vs `RemoteIP` (Device*). Casing matters.

Reference: [KQL overview](https://learn.microsoft.com/en-us/kusto/query/?view=microsoft-sentinel) ·
[best practices](https://learn.microsoft.com/en-us/kusto/query/best-practices?view=microsoft-sentinel) ·
[optimize log queries](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/query-optimization)
