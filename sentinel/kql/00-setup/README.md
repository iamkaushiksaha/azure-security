# Stage 00 · Setup — Get a dataset you can actually practise on

> **The problem this solves:** Almost every KQL tutorial says "run this against `SigninLogs`" — but a new or quiet Microsoft Sentinel workspace has **little or no data**, so those queries return nothing and you can't learn. This stage gives you a realistic, deterministic dataset **without waiting for connectors to ingest anything**.

You only do this **once**. Pick the path that matches your situation:

| Your situation | Use | Cost |
|---|---|---|
| You have a Sentinel / Log Analytics workspace (even empty) | **Method 1 — Seed a function** | Free |
| You have **no** Azure subscription at all | **Method 2 — Azure Data Explorer free cluster + CSV** | Free, no subscription/credit card |

Both methods create the same object — a queryable thing called **`DemoIdentityLogs`** — so **every later lab works identically** regardless of which path you chose.

---

## The dataset

5 users · 2 event types · 20 records. The same story runs through every example so you build intuition instead of memorising disconnected snippets.

| User | What they do in the data |
|---|---|
| `alexw@contoso.com` | Repeated failed sign-ins from a Netherlands IP (`185.220.101.2`), then failed admin role assignments — a **compromise narrative** |
| `meganb@contoso.com` | Clean successful sign-ins from the UK |
| `sophial@contoso.com` | Disabled-account and expired-password failures from Germany |
| `jamest@contoso.com` | A failed-then-succeeded login (typo, then success) |
| `itadmin@contoso.com` | Legitimate admin operations (group/user management) from India |

**Columns:** `TimeGenerated`, `EventType` (Signin/Audit), `UserPrincipalName`, `IPAddress`, `AppDisplayName`, `ResultType`, `ResultDescription`, `RiskLevelDuringSignIn`, `Location`, `OperationName`, `AuditResult`, `Category`.

> ⚠️ **One thing to know up front:** in this demo dataset `ResultType` is an **integer** (`0` = success). In the **real** `SigninLogs` table it's a **string** (`"0"` = success). So you'll use `ResultType != 0` here and `ResultType != "0"` in production. This is the single most common beginner trip-up — see [`../reference/schema-gotchas.md`](../reference/schema-gotchas.md). Confirmed in the [SigninLogs table reference](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/signinlogs).

---

## Method 1 — Seed a function in Sentinel / Log Analytics

This creates a **saved function** from a `datatable()`. No ingestion, no waiting.

1. Open **Microsoft Sentinel → Logs** (or **Log Analytics → Logs**), and make sure the editor is in **KQL mode**.
2. Open [`seed-DemoIdentityLogs.kql`](seed-DemoIdentityLogs.kql), copy **Method A** (the whole `datatable(...)` block), paste it into the query editor, and select **Run**. You'll see 20 rows.
3. In the results pane, select **Save → Save as function**.
4. Fill in:
   - **Function name:** `DemoIdentityLogs`
   - **Legacy category:** `Functions`
   - Leave *Save as computer group* unchecked and *Function parameters* empty.
5. Select **Save**.

**Verify** — open a new query tab and run:

```kusto
DemoIdentityLogs
| take 10
```

You should immediately see demo sign-in and audit records. **Keep the Time range at `Last 7 days`** for all later labs.

> **Why the data is always "recent":** the seed query ends with `extend TimeGenerated = now() - Offset`. `now()` re-evaluates on every run, so the rows are always a few hours old — comfortably inside any `ago(7d)` filter.
>
> Reference: [Save a query as a function](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/functions) · [datatable operator](https://learn.microsoft.com/en-us/kusto/query/datatable-operator?view=microsoft-sentinel)

---

## Method 2 — Azure Data Explorer free cluster + CSV

No Azure subscription? Azure Data Explorer (ADX) gives **anyone with a Microsoft account a free cluster** — no subscription, no credit card, ~100 GB storage, valid for a year (auto-extends). It speaks the **same KQL** as Sentinel.
Source: [What is a free Azure Data Explorer cluster?](https://learn.microsoft.com/en-us/azure/data-explorer/start-for-free)

### 2a. Create your free cluster (one time, ~2 minutes)

1. Go to **https://aka.ms/kustofree** and sign in with a Microsoft account or Entra identity.
2. Create the free cluster — it provisions a cluster **and** a database for you.
   Reference: [Create a free cluster (web UI)](https://learn.microsoft.com/en-us/azure/data-explorer/start-for-free-web-ui)

### 2b. Load the CSV (UI path — easiest)

1. In the [ADX web UI](https://dataexplorer.azure.com/home), select **Query** in the left pane.
2. **Right-click your database → Get data**.
3. Source = **Local file**. Target = **+ New table** named `DemoIdentityLogsRaw`.
4. **Browse** and select [`csv/demo_identity_logs.csv`](csv/demo_identity_logs.csv) → **Next**.
5. On the **Inspect** tab, tick **First row header** so the column names map correctly → **Finish**.

Reference: [Get data from a local file](https://learn.microsoft.com/en-us/azure/data-explorer/get-data-file)

### 2c. Create the time-rebasing function

The CSV stores an `Offset` (e.g. `06:00:00`) instead of a timestamp, so the data never goes stale. Turn it into the same `DemoIdentityLogs` the labs expect by pasting this **control command** ([`csv/load-into-adx.kql`](csv/load-into-adx.kql) has it too):

```kusto
.create-or-alter function DemoIdentityLogs() {
    DemoIdentityLogsRaw
    | extend TimeGenerated = now() - totimespan(Offset)
    | project-away Offset
}
```

**Verify:**

```kusto
DemoIdentityLogs
| take 10
```

> Prefer commands over clicking? [`csv/load-into-adx.kql`](csv/load-into-adx.kql) creates the table, ingests, and builds the function end-to-end.

---

## Done — what's next

You now have `DemoIdentityLogs`. Continue to **[Stage 01 · Basics](../01-basics/README.md)**.

When you eventually have real data flowing into Sentinel, Stages 03–04 switch to the real tables (`SigninLogs`, `AuditLogs`, `DeviceProcessEvents`, …) — and you'll already know the operators cold.
