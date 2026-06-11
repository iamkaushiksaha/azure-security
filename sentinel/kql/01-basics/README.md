# Stage 01 · Basics — Learn to *think* in KQL

> **Audience:** complete beginners and SOC Tier 1 analysts.
> **Goal:** read and write KQL as a sequence of transformations — not memorise snippets.
> **Prerequisite:** finish [Stage 00 · Setup](../00-setup/README.md) so `DemoIdentityLogs` exists. Every query here runs against it, so you'll see real results immediately.

---

## 1. What KQL is

Kusto Query Language (**KQL**) is a **read-only** language for exploring large volumes of log/telemetry data. It powers **Microsoft Sentinel**, **Azure Monitor / Log Analytics**, **Microsoft Defender**, and **Azure Data Explorer** — learn it once, use it everywhere.
Reference: [KQL overview](https://learn.microsoft.com/en-us/kusto/query/?view=microsoft-sentinel)

## 2. The mental model: a pipeline

A KQL query starts with a **table** and flows **top-to-bottom** through `|` (pipe) operators. Each operator takes the rows from the line above and transforms them.

```text
TableName          ← start with a data source
| where ...        ← filter rows (cut noise early)
| extend ...       ← add computed columns
| summarize ...    ← aggregate / group
| sort by ...      ← order
| project ...      ← choose columns to display
```

Read this query like a sentence — *"take DemoIdentityLogs, keep only failed sign-ins, count them per user, show the worst first"*:

```kusto
DemoIdentityLogs
| where EventType == "Signin"
| where ResultType != 0
| summarize FailedAttempts = count() by UserPrincipalName
| sort by FailedAttempts desc
```

> **Golden rule:** filter **early**. The sooner you cut rows with `where`, the faster and cheaper the query.

## 3. Always start with `take`

Before writing logic, look at the shape of the data. `take` grabs a few arbitrary rows so you can see the columns and values safely:

```kusto
DemoIdentityLogs
| take 10
```

## 4. Filtering with `where`

`where` keeps only rows that match a condition.

```kusto
// Only sign-in events
DemoIdentityLogs
| where EventType == "Signin"
```

```kusto
// Only FAILED sign-ins (ResultType is an int in the demo set; 0 = success)
DemoIdentityLogs
| where EventType == "Signin"
| where ResultType != 0
```

Common operators inside `where`:

| Operator | Meaning | Example |
|---|---|---|
| `==`, `!=` | exact equality (case-sensitive) | `EventType == "Audit"` |
| `=~`, `!~` | equality, **case-insensitive** | `Location =~ "germany"` |
| `in`, `!in` | match any value in a list | `ResultType in (50126, 50053)` |
| `contains`, `has` | substring / whole-token match | `ResultDescription has "password"` |
| `>`, `<`, `>=` | comparisons (numbers, dates) | `TimeGenerated > ago(1d)` |

> `has` is **faster** than `contains` — it matches whole tokens and uses the index. Prefer `has` when you can.
> Reference: [String operators](https://learn.microsoft.com/en-us/kusto/query/datatypes-string-operators?view=microsoft-sentinel)

## 5. Time filtering & query hygiene

Every real investigation starts with **time**. `ago()` is a relative time expression.

```kusto
DemoIdentityLogs
| where TimeGenerated > ago(7d)
```

> ⚠️ Forgetting a time filter is the #1 cause of slow, expensive queries on real data. Make it a reflex.
> Reference: [ago() function](https://learn.microsoft.com/en-us/kusto/query/ago-function?view=microsoft-sentinel)

## 6. Choosing columns with `project`

`project` selects (and orders, and renames) the columns you want to see. It makes results readable.

```kusto
DemoIdentityLogs
| where EventType == "Signin"
| where ResultType != 0
| project TimeGenerated, UserPrincipalName, IPAddress, AppDisplayName, ResultDescription
```

Related: `project-away` removes columns; `project-rename` renames them.

## 7. Adding logic with `extend`

`extend` creates a **new computed column** from existing data.

```kusto
DemoIdentityLogs
| where EventType == "Signin"
| extend Outcome = iff(ResultType == 0, "Success", "Failure")
| project TimeGenerated, UserPrincipalName, Outcome, ResultDescription
```

`iff(condition, valueIfTrue, valueIfFalse)` is the inline if. For many branches, use `case()`.
Reference: [iff()](https://learn.microsoft.com/en-us/kusto/query/iff-function?view=microsoft-sentinel) · [case()](https://learn.microsoft.com/en-us/kusto/query/case-function?view=microsoft-sentinel)

## 8. Reusable values with `let`

`let` names a value or a sub-result so you don't repeat yourself and the intent is clear.

```kusto
let lookback = 7d;
let failureCodes = dynamic([50126, 50053, 50057, 50055]);
DemoIdentityLogs
| where EventType == "Signin"
| where TimeGenerated > ago(lookback)
| where ResultType in (failureCodes)
| project TimeGenerated, UserPrincipalName, ResultType, ResultDescription, IPAddress, Location
| sort by TimeGenerated desc
```

Reference: [let statement](https://learn.microsoft.com/en-us/kusto/query/let-statement?view=microsoft-sentinel)

## 9. Free-text search with `search`

When you don't know which column holds a value, `search` scans them all. Great for exploration, slower than a targeted `where` — switch to `where` once you know the column.

```kusto
DemoIdentityLogs
| search "Failure"
```

---

## Core operators to memorise

| Operator | Why it matters |
|---|---|
| `where` | Reduce noise early |
| `project` / `project-away` | Control which columns show |
| `extend` | Add calculated columns |
| `summarize` | Aggregate (next stage) |
| `sort by` (`order by`) | Prioritise results |
| `take` / `limit` | Sample data safely |
| `search` | Explore when you don't know the column |
| `let` | Reuse values, self-document |

---

## 🧪 Exercises

Try these against `DemoIdentityLogs` before peeking at the answers.

1. Show only the **audit** events, newest first, displaying time, user, operation, and result.
2. List every **failed** sign-in from a `medium` or `high` risk level.
3. For sign-ins, add a column `Country` equal to `Location`, and show only sign-ins **not** from the United States.
4. Find any record (sign-in or audit) that mentions the word `password`.

<details>
<summary><b>Answers</b></summary>

```kusto
// 1
DemoIdentityLogs
| where EventType == "Audit"
| project TimeGenerated, UserPrincipalName, OperationName, AuditResult
| sort by TimeGenerated desc
```
```kusto
// 2
DemoIdentityLogs
| where EventType == "Signin"
| where ResultType != 0
| where RiskLevelDuringSignIn in ("medium", "high")
| project TimeGenerated, UserPrincipalName, IPAddress, RiskLevelDuringSignIn, ResultDescription
```
```kusto
// 3
DemoIdentityLogs
| where EventType == "Signin"
| extend Country = Location
| where Country != "United States"
| project TimeGenerated, UserPrincipalName, Country, AppDisplayName
```
```kusto
// 4
DemoIdentityLogs
| search "password"
```
</details>

---

## Common beginner mistakes

- Filtering before you understand the columns → always `take 10` first.
- Forgetting `TimeGenerated` filters → slow queries on real data.
- Using `==` when the real `SigninLogs.ResultType` needs `"0"` (string) → see [schema-gotchas](../reference/schema-gotchas.md).
- Copy-pasting queries without reading them line by line.

**Next:** [Stage 02 · Aggregation & Visualization](../02-aggregation-viz/README.md) — turn rows into insight with `summarize`, `bin()`, and `render`.

Reference hub: [Learn common KQL operators](https://learn.microsoft.com/en-us/kusto/query/tutorials/learn-common-operators?view=microsoft-sentinel)
