# Stage 02 · Aggregation & Visualization — Turn rows into insight

> **Goal:** group, count, and chart data with `summarize`, `bin()`, and `render`, then correlate across event types with `union` and `join`.
> **Prerequisite:** `DemoIdentityLogs` from [Stage 00](../setup/README.md). All queries run against it.

---

## 1. `summarize` — the workhorse

`summarize` collapses many rows into grouped aggregates. Pattern: `summarize <Aggregation> by <GroupingColumns>`.

```kusto
// Failed sign-ins per user
DemoIdentityLogs
| where EventType == "Signin"
| where ResultType != 0
| summarize FailureCount = count() by UserPrincipalName
| sort by FailureCount desc
```

Group by **multiple** columns to slice finer:

```kusto
// Failures per user AND source IP — surfaces where the attempts came from
DemoIdentityLogs
| where EventType == "Signin"
| where ResultType != 0
| summarize FailureCount = count() by UserPrincipalName, IPAddress
| sort by FailureCount desc
```

Reference: [summarize operator](https://learn.microsoft.com/en-us/kusto/query/summarize-operator?view=microsoft-sentinel) · [Aggregation functions](https://learn.microsoft.com/en-us/kusto/query/aggregation-functions?view=microsoft-sentinel)

## 2. The aggregation functions you'll use most

| Function | What it gives you | Example |
|---|---|---|
| `count()` | number of rows in the group | `summarize n = count() by UserPrincipalName` |
| `countif(pred)` | conditional count | `summarize Fails = countif(ResultType != 0) by UserPrincipalName` |
| `dcount(col)` | approx. distinct values | `summarize Apps = dcount(AppDisplayName) by UserPrincipalName` |
| `arg_max(t, *)` | the whole row with the max of `t` | `summarize arg_max(TimeGenerated, *) by UserPrincipalName` |
| `make_set(col)` | de-duplicated list | `summarize IPs = make_set(IPAddress) by UserPrincipalName` |
| `make_list(col)` | list keeping duplicates/order | `summarize Ops = make_list(OperationName) by UserPrincipalName` |

```kusto
// Distinct apps each user FAILED against (>1 hints at spray / probing)
DemoIdentityLogs
| where EventType == "Signin"
| where ResultType != 0
| summarize DistinctApps = dcount(AppDisplayName) by UserPrincipalName
| where DistinctApps > 1
| sort by DistinctApps desc
```

```kusto
// Latest sign-in record per user (arg_max carries all columns via *)
DemoIdentityLogs
| where EventType == "Signin"
| summarize arg_max(TimeGenerated, *) by UserPrincipalName
| project UserPrincipalName, TimeGenerated, ResultType, IPAddress, Location, AppDisplayName
```

```kusto
// Distinct IPs per user (make_set) vs. ordered operation list (make_list)
DemoIdentityLogs
| where EventType == "Signin" and ResultType == 0
| summarize IPAddresses = make_set(IPAddress) by UserPrincipalName
```

> `make_set` removes duplicates (good for "which IPs?"); `make_list` keeps every occurrence in order (good for "the sequence of actions").

## 3. Time bucketing with `bin()`

`bin(column, size)` rounds values **down** to a fixed interval — essential for time series.

```kusto
// Sign-in failures per hour
DemoIdentityLogs
| where EventType == "Signin" and ResultType != 0
| summarize Failures = count() by bin(TimeGenerated, 1h)
```

Change the size to suit the span: `5m`, `1h`, `1d`. Reference: [bin()](https://learn.microsoft.com/en-us/kusto/query/bin-function?view=microsoft-sentinel)

## 4. Charts with `render`

Append `render` to draw the result inline. The **first column** decides the X-axis; numeric columns are the values.

```kusto
// Bar chart: failures by user
DemoIdentityLogs
| where EventType == "Signin" and ResultType != 0
| summarize Failures = count() by UserPrincipalName
| sort by Failures desc
| render barchart
```

```kusto
// Time chart: failures over time
DemoIdentityLogs
| where EventType == "Signin" and ResultType != 0
| summarize Failures = count() by bin(TimeGenerated, 1h)
| render timechart
```

```kusto
// Pie chart: share of attempts by application
DemoIdentityLogs
| where EventType == "Signin"
| summarize Count = count() by AppDisplayName
| render piechart
```

```kusto
// Multi-series: success vs failure on one time chart.
// A string column (Outcome) after the numeric column splits it into series.
DemoIdentityLogs
| where EventType == "Signin"
| extend Outcome = iff(ResultType == 0, "Success", "Failure")
| summarize Count = count() by bin(TimeGenerated, 1h), Outcome
| render timechart
```

> **Shape matters for charts.** Timechart = first column `datetime`, then a numeric, then (optionally) one string column for series. Barchart/piechart = first column the category, second column numeric. Reduce to the columns the chart needs with `project`.
> Reference: [render operator](https://learn.microsoft.com/en-us/kusto/query/render-operator?view=microsoft-sentinel)

## 5. Combining tables: `union`

`union` stacks rows from multiple sources. In the demo set, both event types live in one table, so we filter — but the same syntax works across real tables (`SigninLogs | union AuditLogs`).

```kusto
// A unified activity feed: who did what, when — from both event types
DemoIdentityLogs
| where EventType == "Signin"
| project TimeGenerated, Actor = UserPrincipalName, Action = strcat("Sign-in: ", ResultDescription), Source = IPAddress
| union (
    DemoIdentityLogs
    | where EventType == "Audit"
    | project TimeGenerated, Actor = UserPrincipalName, Action = OperationName, Source = AuditResult
)
| sort by TimeGenerated desc
```

Reference: [union operator](https://learn.microsoft.com/en-us/kusto/query/union-operator?view=microsoft-sentinel)

## 6. Correlating with `join`

`join` matches rows across two result sets on a key. This is how you connect *failed logins* to *admin activity by the same user* — the heart of detection.

```kusto
// Users with >1 failed sign-in who ALSO performed admin operations
let FailedUsers =
    DemoIdentityLogs
    | where EventType == "Signin" and ResultType != 0
    | summarize FailureCount = count() by UserPrincipalName
    | where FailureCount > 1;
DemoIdentityLogs
| where EventType == "Audit"
| join kind=inner FailedUsers on UserPrincipalName
| project TimeGenerated, UserPrincipalName, OperationName, AuditResult, FailureCount
| sort by TimeGenerated desc
```

Join flavours you'll meet: `inner` (only matches), `leftouter` (all left + matches — enrichment), `leftanti` (left rows with **no** match — "find what's missing"). Full treatment in [Stage 03](../advanced/README.md).
Reference: [join operator](https://learn.microsoft.com/en-us/kusto/query/join-operator?view=microsoft-sentinel)

---

## 🧪 Exercises

1. Count **total** vs **failed** sign-ins per user in a single `summarize` (hint: `count()` + `countif()`).
2. Build a bar chart of the **top audit operations** by frequency.
3. For each user, list the **set of countries** (`Location`) they signed in from.
4. Plot sign-in **failures per hour**, but only for `alexw@contoso.com`.

<details>
<summary><b>Answers</b></summary>

```kusto
-- 1
DemoIdentityLogs
| where EventType == "Signin"
| summarize Total = count(), Failed = countif(ResultType != 0) by UserPrincipalName
| sort by Failed desc
```
```kusto
-- 2
DemoIdentityLogs
| where EventType == "Audit"
| summarize Count = count() by OperationName
| sort by Count desc
| render barchart
```
```kusto
-- 3
DemoIdentityLogs
| where EventType == "Signin"
| summarize Countries = make_set(Location) by UserPrincipalName
```
```kusto
-- 4
DemoIdentityLogs
| where EventType == "Signin" and ResultType != 0 and UserPrincipalName == "alexw@contoso.com"
| summarize Failures = count() by bin(TimeGenerated, 1h)
| render timechart
```
</details>

---

**Next:** [Stage 03 · Advanced](../advanced/README.md) — parsing dynamic data, modular `let`, ASIM parsers, and visualization shaping on the **real** tables.
