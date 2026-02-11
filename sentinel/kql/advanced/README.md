# Advanced KQL Usage in Microsoft Sentinel

## Aggregation Functions: Advanced Summarization and Metrics

Beyond basic counts and sums, Kusto Query Language offers rich
aggregation functions for deeper analysis. You can calculate percentiles
to understand data distribution, use conditional counts with
`countif()`, get approximate unique counts with `dcount()`, compute
averages with `avg()`, and even retrieve entire records with `arg_max()`
or `arg_min()`. These functions are used with the `summarize` operator
and can be combined in one query for multiple
metrics[\[1\]](https://learn.microsoft.com/en-us/kusto/query/aggregation-functions?view=microsoft-fabric#:~:text=count,of%20the%20group%20elements%2C%20an)[\[2\]](https://learn.microsoft.com/en-us/kusto/query/aggregation-functions?view=microsoft-fabric#:~:text=dcount,value%20across%20the%20group%20without%2Fwith).
For example, to analyze sign-in events by user:

    SigninLogs
    | where TimeGenerated > ago(7d)
    | summarize TotalLogins = count(), FailedLogins = countif(ResultType != 0) by UserPrincipalName
    | sort by FailedLogins desc

This query counts total logins per user and how many were failures
(using `countif` for ResultType not equal to success). We could also
calculate percentiles of a numeric field (e.g. login duration) with
`percentile()` or multiple percentiles with `percentiles()` for more
insight[\[3\]](https://learn.microsoft.com/en-us/kusto/query/aggregation-functions?view=microsoft-fabric#:~:text=a%20predicate,a%20sample%20without%2Fwith%20a%20predicate).
For instance, to see variation in a hypothetical *Duration* field:

    SigninLogs
    | summarize p50=percentile(Duration, 50), p95=percentile(Duration, 95) 

If you need the latest record per group (e.g. the most recent login for
each user), use `arg_max()`. For example, the query below finds the last
login time, IP, and app used by each user:

    SigninLogs
    | summarize arg_max(TimeGenerated, IPAddress, AppDisplayName) by UserPrincipalName

The `arg_max()` function returns the *other* fields from the record
where *TimeGenerated* was maximal, effectively giving the latest login
info per
user[\[4\]](https://learn.microsoft.com/en-us/kusto/query/arg-max-aggregation-function?view=microsoft-fabric#:~:text=Learn%20learn,function%20differs%20from%20the).
Using these advanced aggregators helps build richer summaries, but
always remember to include a time filter (e.g.
`TimeGenerated > ago(7d)`) to work on relevant data and reduce scanning
cost[\[5\]](file://file_00000000c3dc7206ab6015d9773582e5#:~:text=%60%60%60kql%20,take%2010).

## Time Bucketing with `bin()` for Time Series

When creating time-series visualizations or trend analyses, it's best to
group data into time buckets. The `bin()` function rounds timestamps
down to a specified interval, allowing you to aggregate by consistent
time
windows[\[6\]](https://learn.microsoft.com/en-us/kusto/query/bin-function?view=microsoft-fabric#:~:text=Rounds%20values%20down%20to%20an,of%20a%20given%20bin%20size).
For example, to see daily sign-in counts:

    SigninLogs
    | where TimeGenerated > ago(30d)
    | summarize LoginCount = count() by bin(TimeGenerated, 1d)

This uses `bin(TimeGenerated, 1d)` to bucket events per day. The result
is suitable for a timeline chart of daily login volume. If you need
hourly or 15-minute granularity, adjust the bin size (e.g.
`bin(TimeGenerated, 1h)` or `15m`). Using `bin()` ensures scattered
timestamps are grouped into uniform
slots[\[7\]](https://learn.microsoft.com/en-us/kusto/query/tutorials/use-aggregation-functions?view=microsoft-fabric#:~:text=To%20aggregate%20by%20numeric%20or,make%20comparisons%20between%20different%20periods).
A quick visualization can then be added:

    ... | render timechart

This would produce a time chart of login counts per day. In KQL, `bin()`
is essentially equivalent to a floor operation on time (or numeric
values)[\[8\]](https://learn.microsoft.com/en-us/kusto/query/bin-function?view=microsoft-fabric#:~:text=Rounds%20values%20down%20to%20an,of%20a%20given%20bin%20size).
Always choose a bin size that makes sense for the data frequency (daily
for long spans, hourly for recent detailed trends, etc.). Bucketing is
crucial for performance and readability, especially in workbooks or
reports -- it prevents generating an overwhelming number of points and
aligns data to regular intervals for clear charts.

## Join Types and Use Cases (Correlations)

KQL supports several join flavors to correlate data across
tables[\[9\]](https://learn.microsoft.com/en-us/kusto/query/join-operator?view=microsoft-fabric#:~:text=JoinFlavor%20,LeftTable%20are%20matched%20with%20rows)[\[10\]](https://learn.microsoft.com/en-us/kusto/query/join-operator?view=microsoft-fabric#:~:text=Join%20flavor%20Returns%20Illustration%20innerunique,tables%2C%20including%20the%20matching%20keys):

-   **Inner Join (**`inner`**)** -- Returns only matching rows from both
    sides. Use this when you want **only correlated events** present in
    both
    datasets[\[11\]](https://learn.microsoft.com/en-us/kusto/query/join-operator?view=microsoft-fabric#:~:text=table%20Image%20%20%2012,from%20the%20right%20table%20Image).
    For example, joining sign-in logs to audit logs on the same user to
    find sign-ins that had a subsequent configuration change.
-   **Left Outer Join (**`leftouter`**)** -- Returns all rows from the
    left side, adding data from the right side when keys
    match[\[12\]](https://learn.microsoft.com/en-us/kusto/query/join-operator?view=microsoft-fabric#:~:text=Schema%3A%20All%20columns%20from%20both,matching%20rows%20from%20the%20left).
    Useful to **enrich** a primary dataset with additional info (e.g.
    take all alerts and join threat intelligence data on an IoC field,
    keeping all alerts regardless of TI match).
-   **Right Outer Join (**`rightouter`**)** -- Opposite of leftouter:
    all rows from the right side plus matches from
    left[\[13\]](https://learn.microsoft.com/en-us/kusto/query/join-operator?view=microsoft-fabric#:~:text=Rows%3A%20All%20records%20from%20the,15%20Full%20outer%20join).
    This is less common in Sentinel, but could be used if you have a
    reference set on the right that you want to ensure all appear.
-   **Anti Join (**`leftanti`**/**`anti`**)** -- Returns rows from the
    left side **that have no match** on the
    right[\[14\]](https://learn.microsoft.com/en-us/kusto/query/join-operator?view=microsoft-fabric#:~:text=leftsemi%20%20Left%20semi%20join,36%20rightsemi%20Right%20semi%20join).
    This \"not exists\" join is great for finding things like accounts
    that logged in interactively but *never* appear in admin activity,
    or IPs seen in one log but not in another.
-   **Lookup** -- A special case of left join optimized for small
    reference tables. The `lookup` operator extends the left (fact)
    table with columns from the right (dimension) without duplicating
    the join
    key[\[15\]](https://learn.microsoft.com/en-us/kusto/query/lookup-operator?view=microsoft-fabric#:~:text=,table%20to%20the).
    It automatically broadcasts the right side (assuming it's small) for
    performance[\[16\]](https://learn.microsoft.com/en-us/kusto/query/lookup-operator?view=microsoft-fabric#:~:text=,table),
    and it doesn't repeat the join keys in output (schema is
    slimmer)[\[17\]](https://learn.microsoft.com/en-us/kusto/query/lookup-operator?view=microsoft-fabric#:~:text=with%20the%20following%20differences%3A)[\[15\]](https://learn.microsoft.com/en-us/kusto/query/lookup-operator?view=microsoft-fabric#:~:text=,table%20to%20the).
    Use `lookup` when enriching large data (left) with a small static
    list or mapping (right), such as tagging alerts with a list of
    high-value assets.

**Best Practices for Joins:** Always time-filter both sides of a join to
avoid scanning all
history[\[5\]](file://file_00000000c3dc7206ab6015d9773582e5#:~:text=%60%60%60kql%20,take%2010)[\[18\]](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/query-optimization#:~:text=let%20MinTime%20%3D%20ago,TimeGenerated%29%20by%20Computer).
For instance, if correlating events, restrict each to a recent timeframe
(e.g. 24 hours) so the join only compares relevant records. Also use
stable, matching keys -- ensure the fields you join on are of the same
type and format. Common stable join keys in Sentinel include user
identifiers (UPN/email), computer names, IP addresses, CorrelationIds,
etc.[\[19\]](file://file_00000000c3dc7206ab6015d9773582e5#:~:text=%2A%2AGood%20join%20keys%3A%2A%2A%20,%E2%86%94%20identity%20tables%20where%20available).
If necessary, normalize case or trim whitespace on join keys (e.g. use
`tolower()` on both sides for case-insensitive matches).

For example, consider correlating Windows logon and logoff events (Event
ID 4624 and 4634 in the SecurityEvent table) to compute session
durations:

    SecurityEvent
    | where TimeGenerated > ago(1d) and EventID == 4624
    | project Computer, AccountName, LogonTime = TimeGenerated
    | join kind=inner (
        SecurityEvent
        | where TimeGenerated > ago(1d) and EventID == 4634
        | project Computer, AccountName, LogoffTime = TimeGenerated
    ) on Computer, AccountName
    | extend SessionDuration = LogoffTime - LogonTime
    | project AccountName, Computer, LogonTime, LogoffTime, SessionDuration

Here we used an inner join on `Computer` and `AccountName` (stable keys
for correlation) and applied the same 24h time filter to both sides. The
result shows only users who have both a logon and logoff, with their
session length computed. If we wanted to instead find logons **without**
a corresponding logoff, we could use a left-anti join (4624 events
leftanti 4634 events on those keys) to get sessions that never logged
off.

In summary, pick the join type that fits the question: inner for
intersections, outer joins for enrichments, anti joins for finding
missing counterparts. And use the `lookup` operator for performance when
one side is a small static table (it avoids heavy shuffle and
duplication)[\[16\]\[20\]](https://learn.microsoft.com/en-us/kusto/query/lookup-operator?view=microsoft-fabric#:~:text=,table).

## Parsing and Extracting Fields (Text and Dynamic Data)

Logs often contain embedded information in strings or dynamic JSON
columns. KQL provides powerful operators to parse these:

-   `parse` **Operator:** Splits a free-form text field into new columns
    using a pattern. It's great for logs with consistent text structure.
    For example, if we have a custom log message like
    `"SrcIP=10.0.0.1; DestIP=10.0.0.5; Action=Allow"`, we can extract
    parts with `parse`:

``` kql
<!-- -->
```

-   | parse Message with "SrcIP=" SrcIp "; DestIP=" DestIp "; Action="
      Action

    This will create columns SrcIp, DestIp, and Action from the message.
    The `parse` operator is like a streamlined multiple `extract` in one
    go, and can use simple text or regex
    patterns[\[21\]](https://learn.microsoft.com/en-us/kusto/query/parse-operator?view=microsoft-fabric#:~:text=The%20,statement)[\[22\]](https://learn.microsoft.com/en-us/kusto/query/parse-operator?view=microsoft-fabric#:~:text=totalSlices%3D,previousLockTime).
    If parsing fails for a row, the new columns are null, so you may
    want to filter those out. Use `parse kind=regex` for full regex
    support or `parse-where` if you only need rows that match the
    pattern[\[23\]](https://learn.microsoft.com/en-us/kusto/query/parse-operator?view=microsoft-fabric#:~:text=Evaluates%20a%20string%20expression%20and,where%20operator).

``` kql
<!-- -->
```

-   `extract()` **Function:** Use this for regex extraction in-line. It
    takes a regex and capture group, and returns the first match. For
    instance, to extract the domain from a username (UPN), one could do:

``` kql
<!-- -->
```

-   SigninLogs \| extend Domain = extract("@(\[\^\\\\\\\"\]+)\$", 1,
    UserPrincipalName)

    This regex finds the substring after the `@`. The third argument is
    the source string, and `1` indicates we want the first captured
    group[\[24\]](https://learn.microsoft.com/en-us/kusto/query/extract-function?view=microsoft-fabric#:~:text=Parameters)[\[25\]](https://learn.microsoft.com/en-us/kusto/query/extract-function?view=microsoft-fabric#:~:text=regex%20,typeof%28long).
    If no match, `extract` returns null. It's useful in `extend` or
    `where` clauses for one-off pattern matching.

``` kql
<!-- -->
```

-   `parse_json()` **(or** `todynamic()`**):** Converts a JSON string
    into a *dynamic* object for easy
    querying[\[26\]](https://learn.microsoft.com/en-us/kusto/query/parse-json-function?view=microsoft-fabric#:~:text=Interprets%20a%20,functions).
    Many Sentinel tables have columns of type `dynamic` (essentially
    JSON data structures). For example, Azure AD logs store details like
    InitiatedBy or TargetResources as JSON. Using `parse_json`, you can
    turn those into dynamic data and then use dot notation to retrieve
    sub-fields:

``` kql
<!-- -->
```

-   AuditLogs \| extend Initiator =
    parse_json(InitiatedBy).user.userPrincipalName \| extend
    TargetObject = parse_json(TargetResources)\[0\].displayName

    Here, InitiatedBy is parsed as JSON and we drill into the
    `userPrincipalName`, and TargetResources (an array) is parsed so we
    take `[0].displayName` of the first target. **Pro tip:** If
    extracting multiple values, it's more efficient to parse the JSON
    once and store it in a dynamic column, then project out fields,
    rather than using multiple `extract_json()`
    calls[\[26\]](https://learn.microsoft.com/en-us/kusto/query/parse-json-function?view=microsoft-fabric#:~:text=Interprets%20a%20,functions)[\[27\]](https://learn.microsoft.com/en-us/kusto/query/parse-json-function?view=microsoft-fabric#:~:text=functions).
    Always cast dynamic fields to a concrete type (string, int, etc.)
    when needed -- e.g. `tostring(parse_json(...))` -- to use them in
    comparisons or joins.

``` kql
<!-- -->
```

-   `mv-expand` **Operator:** Expands multi-value dynamic arrays or
    property bags into multiple
    rows[\[28\]](https://learn.microsoft.com/en-us/kusto/query/mv-expand-operator?view=microsoft-fabric#:~:text=Expands%20multi,property%20bags%20into%20multiple%20records).
    Use this when a field contains an array of values or repeating
    sections. For example, in AuditLogs, `TargetResources` is an array
    of affected objects. To count changes per target, you could do:

``` kql
<!-- -->
```

-   AuditLogs \| mv-expand TargetResource = TargetResources \| extend
    ResourceName = tostring(TargetResource.displayName) \| summarize
    Changes=count() by ResourceName

    Each element in the TargetResources array becomes a separate row
    (duplicating the other
    columns)[\[29\]](https://learn.microsoft.com/en-us/kusto/query/mv-expand-operator?view=microsoft-fabric#:~:text=%60mv,the%20records%20in%20the%20output).
    This makes it easy to aggregate or filter within arrays. Similarly,
    if you had a comma-separated list in a string, you could `split()`
    it into a dynamic array and then mv-expand. Remember that after
    `mv-expand`, the context is one element -- in the above, we expanded
    into a `TargetResource` dynamic object for each, then extracted its
    displayName. `mv-expand` is powerful for working with nested data,
    but use it only when needed, as it can significantly increase row
    counts (consider filtering *before* expanding to minimize overhead).

In summary, use `parse`/`extract` for text patterns, and
`parse_json`/`mv-expand` for JSON or array fields. Combining these
techniques allows you to normalize messy data on the fly (e.g.
extracting IOC values from a log line, or expanding a JSON array of
alerts) and make them available for filtering and aggregation. Always
test your parse patterns to ensure they match expected log formats, and
remember that unparsed values will result in nulls which you might need
to handle with a `where` filter or `ifempty()` function.

## Subqueries and Modular Design with `let`

Complex queries can be broken into simpler, reusable parts using `let`
statements. The `let` statement allows you to assign a name to a
subquery or expression and then reference it later, improving
readability and avoid repeating
logic[\[30\]](https://rodtrent.substack.com/p/fine-tuning-kql-query-performance#:~:text=Fine,Modularization%20allows%20you%20to).
This modular approach is analogous to creating a temp view or variable
in SQL.

For example, suppose we want to find users with more than 5 failed
sign-in attempts in the last day. We can calculate the failures per user
as one step, then filter it:

    let failedCountByUser = 
        SigninLogs
        | where TimeGenerated > ago(1d) and ResultType != 0
        | summarize FailedCount = count() by UserPrincipalName;
    failedCountByUser
    | where FailedCount > 5

Here we defined `failedCountByUser` as the intermediate result (a small
table of users and their failure counts), then queried that result to
get the ones above our threshold. This makes the intent clear -- first
compute counts, then filter -- and it avoids writing the aggregation
twice. The output is simply the list of UPNs with more than five
failures.

Another benefit of `let` is consistency in filters or calculations
across multiple parts of a query. For instance, if you're correlating
two tables and want to ensure both sides use the exact same time window
or criteria, you can define those criteria once. Take a scenario with
union and time filters:

    // BAD: time filter applied after union – each side scans all data
    Heartbeat 
    | summarize arg_min(TimeGenerated, *) by Computer
    | union (Perf | summarize arg_min(TimeGenerated, *) by Computer)
    | where TimeGenerated > ago(1d)

In the above (bad) example, the `where` was applied after the union, so
the summarize on each table scanned all time. We can fix this by scoping
the time filter inside each subquery using
`let`[\[31\]](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/query-optimization#:~:text=Another%20example%20of%20this%20fault,statement%20to%20ensure%20scoping%20consistency)[\[18\]](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/query-optimization#:~:text=let%20MinTime%20%3D%20ago,TimeGenerated%29%20by%20Computer):

    let MinTime = ago(1d);
    Heartbeat 
    | where TimeGenerated > MinTime
    | summarize arg_min(TimeGenerated, *) by Computer
    | union (
        Perf 
        | where TimeGenerated > MinTime
        | summarize arg_min(TimeGenerated, *) by Computer
    )

By defining `MinTime` once, we ensure both Heartbeat and Perf only
consider the last 1 day of data before
unioning[\[18\]](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/query-optimization#:~:text=let%20MinTime%20%3D%20ago,TimeGenerated%29%20by%20Computer).
This not only gives the correct result but also dramatically reduces
resource usage, since each table is time-filtered early (avoid scanning
older
data)[\[5\]](file://file_00000000c3dc7206ab6015d9773582e5#:~:text=%60%60%60kql%20,take%2010).

You can also use `let` to store scalar values (with the help of
functions like `toscalar()`). For example, to compute the percentage of
events that are errors, you might do:

    let totalEvents = toscalar(MyTable | summarize count());
    MyTable
    | summarize Errors=countif(Level == "Error")
    | extend ErrorPercent = 100.0 * todouble(Errors) / totalEvents

Here `totalEvents` is a single number materialized by `toscalar(...)`,
then reused in the
calculation[\[32\]](https://learn.microsoft.com/en-us/kusto/query/tutorials/use-aggregation-functions?view=microsoft-fabric#:~:text=Calculate%20percentage%20based%20on%20two,columns)[\[33\]](https://learn.microsoft.com/en-us/kusto/query/tutorials/use-aggregation-functions?view=microsoft-fabric#:~:text=Run%20the%20query).
This avoids having to re-run the count for every row of the summary (or
doing a join).

**Performance considerations:** Using `let` for subqueries does not
create indexes or temp tables; it's essentially a query alias. The Kusto
engine will inline or optimize the subquery, sometimes even running them
in parallel if used multiple times. However, if the subquery is
expensive, using it multiple times might recompute it multiple times. In
many cases the engine will cache results of a `let` if it's used twice,
but this isn't guaranteed. If you find yourself reusing a heavy subquery
many times, consider materializing it with `materialize()` or
redesigning the query. In general, though, `let` helps **reduce
duplication** of logic and **clarify** intent, which often leads to
fewer mistakes and easier tuning.

Finally, remember that each `let` has scope limited to the query and
later statements. It's good practice to give subqueries descriptive
names (e.g. `HighRiskUsers`, `RecentAdmins`) to self-document the query.
Modular design with `let` will make your KQL easier to read, share, and
modify as requirements change.

## ASIM (Advanced Security Information Model) for Normalized Data

Microsoft Sentinel's Advanced Security Information Model (ASIM) provides
a standardized schema for various event types (DNS, HTTP,
authentication, etc.) and comes with **unifying parsers** (KQL
functions) prefixed with `_Im_` that project your data into these
schemas. Instead of querying raw tables (which differ by data source),
you can use ASIM parsers (functions) to query *by activity type*. This
means a single query can work across multiple sources that have a parser
for that
schema[\[34\]](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers#:~:text=Use%20Advanced%20Security%20Information%20Model,relevant%20parser%20for%20each%20schema)[\[35\]](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers#:~:text=When%20using%20ASIM%20in%20your,the%20specific%20schema%20it%20serves).

**Using** `_Im_*` **Parsers:** Each ASIM parser is named `_Im_<Schema>`
(for built-in, Microsoft-provided parsers) -- for example, `_Im_DNS`,
`_Im_Authentication`, `_Im_WebSession`. You invoke them like a function
in your query. For instance, to query all DNS events in a normalized
way:

    // Using ASIM DNS schema parser
    Im_Dns(starttime=ago(1d), ResponseCodeName="NXDOMAIN")
    | summarize count() by SrcIpAddr, bin(TimeGenerated, 15m)

In this example, `_Im_Dns` pulls data from all DNS logs (Windows DNS,
Linux DNS, etc. that have parsers) and normalizes field names like
`ResponseCodeName` and
`SrcIpAddr`[\[36\]](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers#:~:text=For%20example%2C%20the%20following%20query,normalized%20fields).
We also passed parameters `starttime=ago(1d)` and a filter for
`ResponseCodeName` to NXDOMAIN. Many ASIM functions support such
**filtering parameters** that apply before parsing, which greatly
improves performance by reducing data to
parse[\[37\]](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers#:~:text=_Im_Dns%28starttime%3Dago%281d%29%2C%20responsecodename%3D%27NXDOMAIN%27%29%20,TimeGenerated%2C15m)[\[38\]](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers#:~:text=Using%20parsers%20might%20affect%20your,not%20using%20normalization%20at%20all).
The above is equivalent to writing a query against each DNS source table
and unioning them, but ASIM did that heavy lifting for us with a
consistent schema.

ASIM normalized fields have intuitive names (e.g. `SrcIpAddr`,
`TargetUserId`, `HttpUrl`, etc.), so analysts do not need to know the
source-specific field names. For example, whether a firewall log calls
the source IP `src_ip` or `s_ip` or `ClientIP` -- the
`_Im_NetworkSession` parser will output it as `SrcIpAddr`. This makes
your KQL queries **portable** across environments and data sources.
Detections and hunting queries written with ASIM parsers will
automatically cover any log source that is normalized to that
schema[\[34\]](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers#:~:text=Use%20Advanced%20Security%20Information%20Model,relevant%20parser%20for%20each%20schema).

**When and Why to Prefer ASIM:** Use ASIM parsers for analytics whenever
possible, especially if your workspace has multiple products or might
onboard new data sources. ASIM ensures your query "speaks the same
language" across all logs. For example, an ASIM query for failed logons
(`_Im_Authentication` where LogonStatus == \"Failure\") would catch
Azure AD sign-in failures, on-premises AD failures, etc., as long as
those sources have parsers. This yields broader detection coverage with
one query. It also means less maintenance -- if a new source is added
(say, a new VPN log with an ASIM parser), your existing queries
immediately include it with no changes.

Another advantage is that Microsoft and the community often provide
out-of-the-box queries in ASIM form, so adopting ASIM lets you directly
use that content. It also encourages good practices like using the
**normalized timestamp (**`TimeGenerated`**) and common entities (User,
Host, IP)** which streamline correlations.

**Performance:** There is some overhead to parsing data at query time,
but ASIM parsers are optimized. By using the provided parameters (like
`starttime`, `endtime`, or specific filters such as `EventResult` or
`Protocol`), the parser will only fetch relevant data, minimizing
work[\[39\]](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers#:~:text=Using%20parsers%20might%20affect%20your,not%20using%20normalization%20at%20all).
In fact, with filtering, ASIM queries can be as fast or faster than raw
queries, because they may automatically apply index hints. As a rule,
always include a `starttime=...` parameter in the `_Im_` function call
(and other filters if
available)[\[37\]](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers#:~:text=_Im_Dns%28starttime%3Dago%281d%29%2C%20responsecodename%3D%27NXDOMAIN%27%29%20,TimeGenerated%2C15m).
If you forget, you could still `| where` after the call, but then the
parser might ingest a larger chunk of data upfront. The ASIM
documentation for each schema lists which parameters are supported. For
example, `_Im_Authentication` supports filtering by start/end time and
**EventResult** (Success/Failure) among others.

In practice, a query using ASIM might look like:

    // Find failed logins by user across any identity provider
    Im_Authentication(starttime=ago(1h), EventResult="Failure")
    | summarize Failures=count() by TargetUserId, AuthenticationProtocol
    | sort by Failures desc

This single query could bring in Azure AD sign-ins, on-prem AD, OAuth
token failures, etc., and give you a consolidated view of failed
authentications in the last hour. Without ASIM, you'd need to union
multiple tables and handle differing field names.

ASIM should be preferred for detection rules and hunting queries because
it future-proofs your content. The only times you might not use ASIM
are: (1) if no parser exists for the data (in which case consider
building one or use raw for now), or (2) in exploratory ad-hoc queries
where you know you only need one specific table and prefer its raw
schema. Even then, once you confirm a hypothesis, converting it to ASIM
makes it production-ready.

In summary, ASIM provides a layer of abstraction over your logs -- think
of it as a normalized lens. It leads to more **portable, maintainable,
and wide-reaching**
queries[\[34\]](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers#:~:text=Use%20Advanced%20Security%20Information%20Model,relevant%20parser%20for%20each%20schema).
By using `_Im_` parsers with proper filtering, you get the benefits with
minimal performance cost, and often a performance gain due to
pre-filtering[\[38\]](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers#:~:text=Using%20parsers%20might%20affect%20your,not%20using%20normalization%20at%20all).
Normalize whenever you can -- your SOC content will be robust to changes
and easier to understand by others.

## Preparing Output for Visualizations (Project and Render)

When building charts or visualizations in Sentinel (via Azure Monitor
workbooks or Log Analytics), the final shape of your query results is
important. You often need to use `project` (or `summarize by ...`) to
ensure the output has the right columns for the intended `render`
operator. The `render` keyword in KQL can produce various visualization
types like timechart, barchart, piechart, etc., each expecting data in a
certain
layout[\[40\]](https://learn.microsoft.com/en-us/kusto/query/render-operator?view=microsoft-fabric#:~:text=barchart%20%20First%20column%20is,56)[\[41\]](https://learn.microsoft.com/en-us/kusto/query/render-operator?view=microsoft-fabric#:~:text=table%20%20Default%20,59).

**Timecharts:** Typically, the first column should be a datetime (the
X-axis), and one or more numeric columns as the Y-axis values. If
there's one numeric column, you get a single line. If there's one
numeric and one string column, the distinct string values will produce
separate lines (grouped series) on the same
chart[\[42\]](https://learn.microsoft.com/en-us/kusto/query/visualization-timechart?view=microsoft-fabric#:~:text=A%20time%20chart%20visual%20is,axis%20is%20always%20time)[\[41\]](https://learn.microsoft.com/en-us/kusto/query/render-operator?view=microsoft-fabric#:~:text=table%20%20Default%20,59).
Additional string columns beyond one are ignored in a
timechart[\[42\]](https://learn.microsoft.com/en-us/kusto/query/visualization-timechart?view=microsoft-fabric#:~:text=A%20time%20chart%20visual%20is,axis%20is%20always%20time).
This means you should reduce your result to at most one grouping
dimension for a time series. For example, to plot logins per hour by
result (success vs failure):

    SigninLogs
    | where TimeGenerated > ago(24h)
    | summarize Count = count() by bin(TimeGenerated, 1h), ResultType
    | render timechart

Here the first column is the binned TimeGenerated (datetime), the second
column is the numeric count, and we have one string column (ResultType)
which will produce separate lines for each result type. We might use
`project TimeGenerated, ResultType, Count` explicitly to order the
columns, but `summarize` already outputs bin(TimeGenerated) first by
default. The `render timechart` knows to use the datetime on X-axis and
plot the Count, grouped by ResultType
values[\[41\]](https://learn.microsoft.com/en-us/kusto/query/render-operator?view=microsoft-fabric#:~:text=table%20%20Default%20,59).

To improve readability, you can rename columns via `project`. For
instance, if your count was an unnamed count or something like `count_`,
you can do
`| project Timestamp=bin(TimeGenerated,1h), LoginCount=count_`. This
way, the chart axes or legend show friendly names (Timestamp,
LoginCount). Using `project` also lets you drop any columns that are not
needed for the visualization (extra columns can confuse the render or
simply be ignored). A common pattern is:
`... | summarize X by Y | project Y, X | render barchart` -- to ensure
the columns are in the order the chart expects.

**Barcharts/Columncharts:** These expect the first column to be the
category (X-axis), which can be a string, datetime, or numeric bucket,
and one or more numeric columns as the values (heights of
bars)[\[43\]](https://learn.microsoft.com/en-us/kusto/query/render-operator?view=microsoft-fabric#:~:text=areachart%20%20Area%20graph,56).
If you have multiple numeric columns, a columnchart will group them as
clusters of bars per category, or a barchart will stack them
horizontally per category. If you have one numeric and one string, it
produces one bar per category. For example, to visualize alert counts by
severity:

    SecurityAlert
    | summarize AlertCount = count() by AlertSeverity
    | project Severity = AlertSeverity, AlertCount
    | render columnchart

This will produce a column chart with X-axis as Severity (Informational,
Low, Medium, High, etc. as categories) and Y-axis as the count of
alerts. We used `project` to rename AlertSeverity to just *Severity* for
a cleaner label, and ensure the output has exactly two columns: Severity
(string) and AlertCount (number). The render knows: first column string
-\> treat as categories, second column numeric -\> height of
bars[\[40\]](https://learn.microsoft.com/en-us/kusto/query/render-operator?view=microsoft-fabric#:~:text=barchart%20%20First%20column%20is,56).

**Piecharts:** Expect the first column to be a category (each slice
name) and second column a numeric value (slice
size)[\[44\]](https://learn.microsoft.com/en-us/kusto/query/render-operator?view=microsoft-fabric#:~:text=columnchart%20%20Like%20,56).
So for a pie, your result should have exactly two columns (e.g. Category
and Total). For example, a quick pie of alert count by severity would
use the same output as above but `render piechart`.

**Project vs. Project-away:** If you have a query that outputs many
columns but you only need a few for the visualization, use `project` to
select only the needed ones. Alternatively, `project-away` can remove
unwanted columns while keeping the rest. The goal is to present the
visualization with just the fields it needs: typically a category and a
value (and a time if it's a timechart). This also reduces noise in the
results view.

**Labels and titles:** The `render ... with (...)` syntax allows setting
chart title, axis labels, legends, etc. (for example:
`| render timechart with(title="Logins over time", xtitle="Date", ytitle="Count", legend=visible)`).
While this is not about `project`, it's part of preparing nice output.
You might use `project` to rename columns to more descriptive names,
which often end up directly as labels. For instance, if you project a
column as "Failed Logins", the space is fine in column name and will
show in legends, but note that in KQL you'd have to quote it if you use
it later. It might be safer to use no spaces in column names and rely on
the `ytitle`/`xtitle` properties for pretty labels.

In practice, always double-check how your data is shaped right before
the `render`. A quick mental check or `.take 5` can show if the first
column is what you expect. For timecharts, ensure it's a datetime type
(if it's a string, convert or it may not plot on the time axis). For
example, if you binned by day and then formatted the day as a string,
the chart might treat it as category, not time -- better to keep it as
actual datetime.

In summary, **shape your query output** for the visualization: pick and
order columns with `project`, use meaningful names, and aggregate
appropriately (one row per category or per time slot). The rendering
engine uses the first column's type to decide X-axis (datetime vs
category) and expects one or more numeric measures
thereafter[\[45\]](https://learn.microsoft.com/en-us/kusto/query/render-operator?view=microsoft-fabric#:~:text=%28numeric%29%20columns%20are%20y,Image).
By following these practices, your charts (timecharts, barcharts, etc.)
will display correctly and convey the intended information clearly.

## Advanced Operators Overview (No Examples)

KQL offers additional advanced operators and functions for specialized
scenarios. Below is a brief overview of some powerful ones you might
encounter:

-   `make-series` -- This operator creates a series (an array of values)
    by aggregating data over a continuous axis (typically
    time)[\[46\]](https://learn.microsoft.com/en-us/kusto/query/make-series-operator?view=microsoft-fabric#:~:text=Create%20series%20of%20specified%20aggregated,values%20along%20a%20specified%20axis).
    It's used for advanced time series analysis, allowing you to create,
    for example, an array of counts per day for each computer. Unlike
    `summarize`, which produces one row per group with a single value,
    `make-series` produces one row per group with a *dynamic array* of
    values (and a corresponding array of the axis times). This is useful
    for scenarios like anomaly detection or forecasting where you need
    the full series in one record. Essentially, `make-series` fills in
    missing time bins with default values (e.g. 0) so that each array is
    complete from the start to end
    time[\[47\]](https://learn.microsoft.com/en-us/kusto/query/series-decompose-anomalies-function?view=microsoft-fabric#:~:text=Name%20Type%20Required%20Description%20Series,The%20possible%20values%20are).
    You'd typically follow `make-series` with functions like series
    stats or render a timechart of multiple series.

-   `series_decompose_anomalies()` -- A function for anomaly detection
    in time series data. It takes a dynamic numerical array (like one
    produced by make-series or collected with `make_list()`) and
    identifies points that are statistically
    anomalous[\[48\]](https://learn.microsoft.com/en-us/kusto/query/series-decompose-anomalies-function?view=microsoft-fabric#:~:text=The%20function%20takes%20an%20expression,extracts%20anomalous%20points%20with%20scores).
    Internally, it decomposes the series into components (trend,
    seasonality, residual) and then flags outliers in the residual. The
    output includes indicators like `ad_flag` (e.g. 1 or -1 for
    positive/negative anomalies) and `ad_score` (a score representing
    how far from
    expected)[\[49\]](https://learn.microsoft.com/en-us/kusto/query/series-decompose-anomalies-function?view=microsoft-fabric#:~:text=Returns).
    In Sentinel, this could be used on aggregated metrics (like network
    bytes over time) to find unusual spikes or dips. There is also a
    corresponding visualization kind "anomalychart" that highlights
    these
    points[\[50\]](https://www.kustoking.com/remote-session-anomaly-detection/#:~:text=Remote%20Session%20Anomaly%20Detection%20with,single%20row%3B%20Use%20a).
    `series_decompose_anomalies` is part of a broader set of series
    functions (including `series_decompose()` for full decomposition and
    `series_outliers()` which it uses under the hood). It's a powerful
    way to add ML-like anomaly detection natively in KQL.

-   `pack()`**/**`bag_pack()` -- These functions create a *dynamic
    property bag* (essentially a JSON object) out of separate columns or
    values[\[51\]](https://learn.microsoft.com/en-us/kusto/query/pack-function?view=microsoft-fabric#:~:text=Creates%20a%20dynamic%20property%20bag,list%20of%20keys%20and%20values).
    In KQL, `pack()` was the older name and `bag_pack()` is the current
    name (with identical usage). For example,
    `bag_pack("Key1", Col1, "Key2", Col2)` will produce a single dynamic
    object `{"Key1": value1, "Key2": value2}` for each
    row[\[52\]](https://learn.microsoft.com/en-us/kusto/query/pack-function?view=microsoft-fabric#:~:text=Run%20the%20query).
    This is useful if you want to combine multiple fields into one (for
    example, packing several columns of an event into an
    `"AdditionalFields"` dynamic column). Sentinel uses this in certain
    custom parser scenarios or when outputting data to notebooks.
    Essentially, it's the inverse of unpacking; you *pack* multiple
    columns into one dynamic structure.

-   `bag_unpack` -- This is a plugin (used with the `evaluate` operator)
    to do the opposite of pack: it **unpacks a dynamic property bag into
    individual
    columns**[\[53\]](https://learn.microsoft.com/en-us/kusto/query/bag-unpack-plugin?view=microsoft-fabric#:~:text=The%20,invoked%20with%20the%20evaluate%20operator).
    If you have a dynamic column with JSON (key-value pairs) and you
    want each top-level property to become its own column,
    `evaluate bag_unpack(yourColumn)` will do
    that[\[53\]](https://learn.microsoft.com/en-us/kusto/query/bag-unpack-plugin?view=microsoft-fabric#:~:text=The%20,invoked%20with%20the%20evaluate%20operator).
    For example, if you have a column DeviceDetail of type dynamic that
    contains `{"os":"Windows","trustType":"AzureAD"}`,
    `bag_unpack(DeviceDetail)` will add new columns os and trustType to
    your result set with those
    values[\[54\]](https://www.cloudsma.com/2024/01/extracting-nested-fields-in-kusto-2-0/#:~:text=When%20I%20read%20%E2%80%9Cparse%20json%E2%80%9D,the%20XML%20column%2C%20converts)[\[55\]](https://sandyzeng.gitbook.io/kql/kql-quick-guide/need-to-practice-more/evaluate/bag_unpack#:~:text=bag_unpack%20,distinct%20UserPrincipalName%2C%20displayName%2C%20operatingSystem%2C%20trustType).
    This is extremely handy for working with nested data without
    manually parsing each field. One thing to note: for performance on
    large datasets, it's recommended to provide an output schema
    (listing which keys to unpack and their types) when using
    bag_unpack[\[56\]](https://learn.microsoft.com/en-us/kusto/query/bag-unpack-plugin?view=microsoft-fabric#:~:text=Performance%20considerations).
    Otherwise, the engine has to inspect many rows to figure out the
    columns, which can be slow. But for quick analysis or moderate data,
    `bag_unpack` is a fast way to flatten JSON. Many Sentinel queries
    use `evaluate bag_unpack()` on the AdditionalFields or Entity
    details in SecurityAlert to quickly get those attributes as columns.

-   **Dynamic Data Type** -- The *dynamic* type in KQL is a flexible
    JSON-like data type that can hold arrays, property bags
    (dictionaries), or primitive
    values[\[57\]](https://learn.microsoft.com/en-us/kusto/query/scalar-data-types/dynamic?view=microsoft-fabric#:~:text=The%20,any%20of%20the%20following%20values).
    It's the type behind all JSON columns in Sentinel (like
    AzureActivity's Properties, or Custom logs). You can think of it as
    "schemaless" in that each row's dynamic object might have different
    keys. You access dynamic fields using JSON dot notation or the
    bracket notation (e.g. `MyDynamicField.Key` or
    `MyDynamicField["Key Name"]`)[\[58\]](https://learn.microsoft.com/en-us/kusto/query/scalar-data-types/dynamic?view=microsoft-fabric#:~:text=To%20subscript%20a%20dictionary%2C%20use,constant%2C%20both%20options%20are%20equivalent)[\[59\]](https://learn.microsoft.com/en-us/kusto/query/scalar-data-types/dynamic?view=microsoft-fabric#:~:text=Expression%20Accessor%20expression%20type%20Meaning,last%20value%20in%20the%20array),
    and you typically cast the result to a concrete type (`tostring()`,
    `toint()`, etc.) once you extract
    it[\[60\]](https://learn.microsoft.com/en-us/kusto/query/scalar-data-types/dynamic?view=microsoft-fabric#:~:text=Casting%20dynamic%20objects)[\[61\]](https://learn.microsoft.com/en-us/kusto/query/scalar-data-types/dynamic?view=microsoft-fabric#:~:text=Expression%20Value%20Type%20X%20parse_json%28%27,01%29%20%60datetime).
    Dynamic is powerful for storing complex data, but queries on it may
    be slower than on typed columns. The functions above (`parse_json`,
    `mv-expand`, `bag_unpack`, etc.) are all about dealing with dynamic
    data. Best practice is to **filter early** on dynamic content if
    possible (for example, if dynamic field has a specific key/value you
    need, try to query it in the where clause after using `parse_json`
    or an index query). Dynamic fields allow a lot of flexibility in
    logs, and mastering their manipulation is key to advanced KQL usage.
    Remember that dynamic arrays are zero-indexed and dynamic property
    bags are unordered sets of
    key-values[\[62\]](https://learn.microsoft.com/en-us/kusto/query/scalar-data-types/dynamic?view=microsoft-fabric#:~:text=,more%20information%2C%20see%20Null%20values).
    When converting dynamic values that contain numbers or dates, Kusto
    will often auto-cast if the string looks like a number or date (for
    example a dynamic value `"123"` might behave as int 123 in
    comparisons)[\[63\]](https://learn.microsoft.com/en-us/kusto/query/scalar-data-types/dynamic?view=microsoft-fabric#:~:text=,value%20mappings%20in%20a),
    but it's safer to explicitly cast.

These advanced operators/functions -- **make-series** for shaping time
series, **series_decompose_anomalies** for detecting anomalies,
**pack/unpack** for working with custom JSON, and the dynamic type
handling -- empower you to perform complex data analysis in Sentinel.
They go beyond simple filtering and counting, enabling scenarios like
trend analysis, anomaly hunting, and working with nested log data. While
not every use case requires them, knowing they exist means you have
tools ready when basic KQL isn't enough. Always refer to official docs
for detailed usage and examples when you employ these in
production[\[46\]](https://learn.microsoft.com/en-us/kusto/query/make-series-operator?view=microsoft-fabric#:~:text=Create%20series%20of%20specified%20aggregated,values%20along%20a%20specified%20axis)[\[48\]](https://learn.microsoft.com/en-us/kusto/query/series-decompose-anomalies-function?view=microsoft-fabric#:~:text=The%20function%20takes%20an%20expression,extracts%20anomalous%20points%20with%20scores),
and test on sample data to ensure you understand the output. Advanced
KQL techniques, combined with the fundamentals, allow you to craft very
powerful queries for threat hunting and security analytics.

[\[1\]](https://learn.microsoft.com/en-us/kusto/query/aggregation-functions?view=microsoft-fabric#:~:text=count,of%20the%20group%20elements%2C%20an)
[\[2\]](https://learn.microsoft.com/en-us/kusto/query/aggregation-functions?view=microsoft-fabric#:~:text=dcount,value%20across%20the%20group%20without%2Fwith)
[\[3\]](https://learn.microsoft.com/en-us/kusto/query/aggregation-functions?view=microsoft-fabric#:~:text=a%20predicate,a%20sample%20without%2Fwith%20a%20predicate)
Aggregation Functions - Kusto \| Microsoft Learn

<https://learn.microsoft.com/en-us/kusto/query/aggregation-functions?view=microsoft-fabric>

[\[4\]](https://learn.microsoft.com/en-us/kusto/query/arg-max-aggregation-function?view=microsoft-fabric#:~:text=Learn%20learn,function%20differs%20from%20the)
arg_max() (aggregation function) - Kusto - Microsoft Learn

<https://learn.microsoft.com/en-us/kusto/query/arg-max-aggregation-function?view=microsoft-fabric>

[\[5\]](file://file_00000000c3dc7206ab6015d9773582e5#:~:text=%60%60%60kql%20,take%2010)
[\[19\]](file://file_00000000c3dc7206ab6015d9773582e5#:~:text=%2A%2AGood%20join%20keys%3A%2A%2A%20,%E2%86%94%20identity%20tables%20where%20available)
sentinel_tables_core_reference.md

<file://file_00000000c3dc7206ab6015d9773582e5>

[\[6\]](https://learn.microsoft.com/en-us/kusto/query/bin-function?view=microsoft-fabric#:~:text=Rounds%20values%20down%20to%20an,of%20a%20given%20bin%20size)
[\[8\]](https://learn.microsoft.com/en-us/kusto/query/bin-function?view=microsoft-fabric#:~:text=Rounds%20values%20down%20to%20an,of%20a%20given%20bin%20size)
bin() - Kusto \| Microsoft Learn

<https://learn.microsoft.com/en-us/kusto/query/bin-function?view=microsoft-fabric>

[\[7\]](https://learn.microsoft.com/en-us/kusto/query/tutorials/use-aggregation-functions?view=microsoft-fabric#:~:text=To%20aggregate%20by%20numeric%20or,make%20comparisons%20between%20different%20periods)
[\[32\]](https://learn.microsoft.com/en-us/kusto/query/tutorials/use-aggregation-functions?view=microsoft-fabric#:~:text=Calculate%20percentage%20based%20on%20two,columns)
[\[33\]](https://learn.microsoft.com/en-us/kusto/query/tutorials/use-aggregation-functions?view=microsoft-fabric#:~:text=Run%20the%20query)
Tutorial: Use aggregation functions in Kusto Query Language - Kusto \|
Microsoft Learn

<https://learn.microsoft.com/en-us/kusto/query/tutorials/use-aggregation-functions?view=microsoft-fabric>

[\[9\]](https://learn.microsoft.com/en-us/kusto/query/join-operator?view=microsoft-fabric#:~:text=JoinFlavor%20,LeftTable%20are%20matched%20with%20rows)
[\[10\]](https://learn.microsoft.com/en-us/kusto/query/join-operator?view=microsoft-fabric#:~:text=Join%20flavor%20Returns%20Illustration%20innerunique,tables%2C%20including%20the%20matching%20keys)
[\[11\]](https://learn.microsoft.com/en-us/kusto/query/join-operator?view=microsoft-fabric#:~:text=table%20Image%20%20%2012,from%20the%20right%20table%20Image)
[\[12\]](https://learn.microsoft.com/en-us/kusto/query/join-operator?view=microsoft-fabric#:~:text=Schema%3A%20All%20columns%20from%20both,matching%20rows%20from%20the%20left)
[\[13\]](https://learn.microsoft.com/en-us/kusto/query/join-operator?view=microsoft-fabric#:~:text=Rows%3A%20All%20records%20from%20the,15%20Full%20outer%20join)
[\[14\]](https://learn.microsoft.com/en-us/kusto/query/join-operator?view=microsoft-fabric#:~:text=leftsemi%20%20Left%20semi%20join,36%20rightsemi%20Right%20semi%20join)
join operator - Kusto \| Microsoft Learn

<https://learn.microsoft.com/en-us/kusto/query/join-operator?view=microsoft-fabric>

[\[15\]](https://learn.microsoft.com/en-us/kusto/query/lookup-operator?view=microsoft-fabric#:~:text=,table%20to%20the)
[\[16\]](https://learn.microsoft.com/en-us/kusto/query/lookup-operator?view=microsoft-fabric#:~:text=,table)
[\[17\]](https://learn.microsoft.com/en-us/kusto/query/lookup-operator?view=microsoft-fabric#:~:text=with%20the%20following%20differences%3A)
[\[20\]](https://learn.microsoft.com/en-us/kusto/query/lookup-operator?view=microsoft-fabric#:~:text=,table)
lookup operator - Kusto \| Microsoft Learn

<https://learn.microsoft.com/en-us/kusto/query/lookup-operator?view=microsoft-fabric>

[\[18\]](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/query-optimization#:~:text=let%20MinTime%20%3D%20ago,TimeGenerated%29%20by%20Computer)
[\[31\]](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/query-optimization#:~:text=Another%20example%20of%20this%20fault,statement%20to%20ensure%20scoping%20consistency)
Optimize log queries in Azure Monitor - Azure Monitor \| Microsoft Learn

<https://learn.microsoft.com/en-us/azure/azure-monitor/logs/query-optimization>

[\[21\]](https://learn.microsoft.com/en-us/kusto/query/parse-operator?view=microsoft-fabric#:~:text=The%20,statement)
[\[22\]](https://learn.microsoft.com/en-us/kusto/query/parse-operator?view=microsoft-fabric#:~:text=totalSlices%3D,previousLockTime)
[\[23\]](https://learn.microsoft.com/en-us/kusto/query/parse-operator?view=microsoft-fabric#:~:text=Evaluates%20a%20string%20expression%20and,where%20operator)
parse operator - Kusto \| Microsoft Learn

<https://learn.microsoft.com/en-us/kusto/query/parse-operator?view=microsoft-fabric>

[\[24\]](https://learn.microsoft.com/en-us/kusto/query/extract-function?view=microsoft-fabric#:~:text=Parameters)
[\[25\]](https://learn.microsoft.com/en-us/kusto/query/extract-function?view=microsoft-fabric#:~:text=regex%20,typeof%28long)
extract() - Kusto \| Microsoft Learn

<https://learn.microsoft.com/en-us/kusto/query/extract-function?view=microsoft-fabric>

[\[26\]](https://learn.microsoft.com/en-us/kusto/query/parse-json-function?view=microsoft-fabric#:~:text=Interprets%20a%20,functions)
[\[27\]](https://learn.microsoft.com/en-us/kusto/query/parse-json-function?view=microsoft-fabric#:~:text=functions)
parse_json() function - Kusto \| Microsoft Learn

<https://learn.microsoft.com/en-us/kusto/query/parse-json-function?view=microsoft-fabric>

[\[28\]](https://learn.microsoft.com/en-us/kusto/query/mv-expand-operator?view=microsoft-fabric#:~:text=Expands%20multi,property%20bags%20into%20multiple%20records)
[\[29\]](https://learn.microsoft.com/en-us/kusto/query/mv-expand-operator?view=microsoft-fabric#:~:text=%60mv,the%20records%20in%20the%20output)
mv-expand operator - Kusto \| Microsoft Learn

<https://learn.microsoft.com/en-us/kusto/query/mv-expand-operator?view=microsoft-fabric>

[\[30\]](https://rodtrent.substack.com/p/fine-tuning-kql-query-performance#:~:text=Fine,Modularization%20allows%20you%20to)
Fine-Tuning KQL Query Performance: Best Practices

<https://rodtrent.substack.com/p/fine-tuning-kql-query-performance>

[\[34\]](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers#:~:text=Use%20Advanced%20Security%20Information%20Model,relevant%20parser%20for%20each%20schema)
[\[35\]](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers#:~:text=When%20using%20ASIM%20in%20your,the%20specific%20schema%20it%20serves)
[\[36\]](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers#:~:text=For%20example%2C%20the%20following%20query,normalized%20fields)
[\[37\]](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers#:~:text=_Im_Dns%28starttime%3Dago%281d%29%2C%20responsecodename%3D%27NXDOMAIN%27%29%20,TimeGenerated%2C15m)
[\[38\]](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers#:~:text=Using%20parsers%20might%20affect%20your,not%20using%20normalization%20at%20all)
[\[39\]](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers#:~:text=Using%20parsers%20might%20affect%20your,not%20using%20normalization%20at%20all)
Use Advanced Security Information Model (ASIM) parsers \| Microsoft
Learn

<https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers>

[\[40\]](https://learn.microsoft.com/en-us/kusto/query/render-operator?view=microsoft-fabric#:~:text=barchart%20%20First%20column%20is,56)
[\[41\]](https://learn.microsoft.com/en-us/kusto/query/render-operator?view=microsoft-fabric#:~:text=table%20%20Default%20,59)
[\[43\]](https://learn.microsoft.com/en-us/kusto/query/render-operator?view=microsoft-fabric#:~:text=areachart%20%20Area%20graph,56)
[\[44\]](https://learn.microsoft.com/en-us/kusto/query/render-operator?view=microsoft-fabric#:~:text=columnchart%20%20Like%20,56)
[\[45\]](https://learn.microsoft.com/en-us/kusto/query/render-operator?view=microsoft-fabric#:~:text=%28numeric%29%20columns%20are%20y,Image)
render operator - Kusto \| Microsoft Learn

<https://learn.microsoft.com/en-us/kusto/query/render-operator?view=microsoft-fabric>

[\[42\]](https://learn.microsoft.com/en-us/kusto/query/visualization-timechart?view=microsoft-fabric#:~:text=A%20time%20chart%20visual%20is,axis%20is%20always%20time)
Time chart visualization - Kusto \| Microsoft Learn

<https://learn.microsoft.com/en-us/kusto/query/visualization-timechart?view=microsoft-fabric>

[\[46\]](https://learn.microsoft.com/en-us/kusto/query/make-series-operator?view=microsoft-fabric#:~:text=Create%20series%20of%20specified%20aggregated,values%20along%20a%20specified%20axis)
make-series operator - Kusto \| Microsoft Learn

<https://learn.microsoft.com/en-us/kusto/query/make-series-operator?view=microsoft-fabric>

[\[47\]](https://learn.microsoft.com/en-us/kusto/query/series-decompose-anomalies-function?view=microsoft-fabric#:~:text=Name%20Type%20Required%20Description%20Series,The%20possible%20values%20are)
[\[48\]](https://learn.microsoft.com/en-us/kusto/query/series-decompose-anomalies-function?view=microsoft-fabric#:~:text=The%20function%20takes%20an%20expression,extracts%20anomalous%20points%20with%20scores)
[\[49\]](https://learn.microsoft.com/en-us/kusto/query/series-decompose-anomalies-function?view=microsoft-fabric#:~:text=Returns)
series_decompose_anomalies() - Kusto \| Microsoft Learn

<https://learn.microsoft.com/en-us/kusto/query/series-decompose-anomalies-function?view=microsoft-fabric>

[\[50\]](https://www.kustoking.com/remote-session-anomaly-detection/#:~:text=Remote%20Session%20Anomaly%20Detection%20with,single%20row%3B%20Use%20a)
Remote Session Anomaly Detection with the Series Decompose \...

<https://www.kustoking.com/remote-session-anomaly-detection/>

[\[51\]](https://learn.microsoft.com/en-us/kusto/query/pack-function?view=microsoft-fabric#:~:text=Creates%20a%20dynamic%20property%20bag,list%20of%20keys%20and%20values)
[\[52\]](https://learn.microsoft.com/en-us/kusto/query/pack-function?view=microsoft-fabric#:~:text=Run%20the%20query)
bag_pack() - Kusto \| Microsoft Learn

<https://learn.microsoft.com/en-us/kusto/query/pack-function?view=microsoft-fabric>

[\[53\]](https://learn.microsoft.com/en-us/kusto/query/bag-unpack-plugin?view=microsoft-fabric#:~:text=The%20,invoked%20with%20the%20evaluate%20operator)
[\[56\]](https://learn.microsoft.com/en-us/kusto/query/bag-unpack-plugin?view=microsoft-fabric#:~:text=Performance%20considerations)
Bag_Unpack Plugin in Azure Data Explorer - Unpack Dynamic Columns -
Kusto \| Microsoft Learn

<https://learn.microsoft.com/en-us/kusto/query/bag-unpack-plugin?view=microsoft-fabric>

[\[54\]](https://www.cloudsma.com/2024/01/extracting-nested-fields-in-kusto-2-0/#:~:text=When%20I%20read%20%E2%80%9Cparse%20json%E2%80%9D,the%20XML%20column%2C%20converts)
Extracting Nested Fields in Kusto 2.0

<https://www.cloudsma.com/2024/01/extracting-nested-fields-in-kusto-2-0/>

[\[55\]](https://sandyzeng.gitbook.io/kql/kql-quick-guide/need-to-practice-more/evaluate/bag_unpack#:~:text=bag_unpack%20,distinct%20UserPrincipalName%2C%20displayName%2C%20operatingSystem%2C%20trustType)
bag_unpack - The Amazing KQL

<https://sandyzeng.gitbook.io/kql/kql-quick-guide/need-to-practice-more/evaluate/bag_unpack>

[\[57\]](https://learn.microsoft.com/en-us/kusto/query/scalar-data-types/dynamic?view=microsoft-fabric#:~:text=The%20,any%20of%20the%20following%20values)
[\[58\]](https://learn.microsoft.com/en-us/kusto/query/scalar-data-types/dynamic?view=microsoft-fabric#:~:text=To%20subscript%20a%20dictionary%2C%20use,constant%2C%20both%20options%20are%20equivalent)
[\[59\]](https://learn.microsoft.com/en-us/kusto/query/scalar-data-types/dynamic?view=microsoft-fabric#:~:text=Expression%20Accessor%20expression%20type%20Meaning,last%20value%20in%20the%20array)
[\[60\]](https://learn.microsoft.com/en-us/kusto/query/scalar-data-types/dynamic?view=microsoft-fabric#:~:text=Casting%20dynamic%20objects)
[\[61\]](https://learn.microsoft.com/en-us/kusto/query/scalar-data-types/dynamic?view=microsoft-fabric#:~:text=Expression%20Value%20Type%20X%20parse_json%28%27,01%29%20%60datetime)
[\[62\]](https://learn.microsoft.com/en-us/kusto/query/scalar-data-types/dynamic?view=microsoft-fabric#:~:text=,more%20information%2C%20see%20Null%20values)
[\[63\]](https://learn.microsoft.com/en-us/kusto/query/scalar-data-types/dynamic?view=microsoft-fabric#:~:text=,value%20mappings%20in%20a)
The dynamic data type - Kusto \| Microsoft Learn

<https://learn.microsoft.com/en-us/kusto/query/scalar-data-types/dynamic?view=microsoft-fabric>
