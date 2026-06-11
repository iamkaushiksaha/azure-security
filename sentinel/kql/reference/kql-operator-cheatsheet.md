# KQL Operator Cheatsheet

A fast lookup for the operators and functions used across this lab. Full docs: [KQL reference](https://learn.microsoft.com/en-us/kusto/query/?view=microsoft-sentinel).

## Filtering & shaping
| Operator | Purpose | Example |
|---|---|---|
| `where` | Filter rows | `where ResultType != "0"` |
| `take` / `limit` | Sample N rows (unordered) | `take 10` |
| `project` | Select / order / rename columns | `project TimeGenerated, UserPrincipalName` |
| `project-away` | Drop columns | `project-away Offset` |
| `project-rename` | Rename columns | `project-rename User = UserPrincipalName` |
| `extend` | Add computed column | `extend Outcome = iff(ResultType==0,"OK","Fail")` |
| `distinct` | Unique combinations | `distinct UserPrincipalName, IPAddress` |
| `sort by` / `order by` | Order rows | `sort by TimeGenerated desc` |
| `top` | Sort + take in one step | `top 10 by Failures desc` |
| `search` | Free-text across columns | `search "Failure"` |

## Aggregation (`summarize`)
| Function | Purpose |
|---|---|
| `count()` | rows in group |
| `countif(pred)` | conditional count |
| `dcount(col)` | approx distinct count |
| `sum()` / `avg()` / `min()` / `max()` | numeric aggregates |
| `arg_max(t, *)` / `arg_min(t, *)` | full row at max/min of `t` |
| `make_set(col)` | de-duplicated list |
| `make_list(col)` | list keeping duplicates/order |
| `percentile(col, n)` | nth percentile |

## Time
| Expression | Purpose |
|---|---|
| `ago(7d)` | relative time (m, h, d) |
| `now()` | current UTC time |
| `bin(TimeGenerated, 1h)` | bucket time for series |
| `startofday()` / `endofday()` | day boundaries |
| `datetime_diff('hour', a, b)` | difference in units |

## Strings
| Operator | Notes |
|---|---|
| `==` / `!=` | case-**sensitive** equality |
| `=~` / `!~` | case-**insensitive** equality |
| `has` / `has_any` | whole-token match (**fast**, indexed) |
| `contains` | substring (slower) |
| `startswith` / `endswith` | prefix / suffix |
| `in` / `in~` | match a list (`~` = case-insensitive) |
| `matches regex` | regex match |

## Multi-table & dynamic
| Operator | Purpose |
|---|---|
| `union` | stack rows from tables |
| `join kind=inner\|leftouter\|leftanti\|...` | correlate on a key |
| `lookup` | enrich large table from small one |
| `parse` | split text into columns |
| `extract(regex, n, src)` | one regex capture |
| `parse_json()` / `todynamic()` | string → dynamic |
| `mv-expand` | array → one row per element |
| `evaluate bag_unpack()` | dynamic bag → columns |

## Visualization
| Render | Expected shape |
|---|---|
| `render timechart` | datetime, numeric(s), ≤1 string (series) |
| `render barchart` / `columnchart` | category, numeric(s) |
| `render piechart` | category, numeric |

## Casting
`tostring()` · `toint()` · `tolong()` · `todouble()` · `todatetime()` · `totimespan()` · `tobool()`
