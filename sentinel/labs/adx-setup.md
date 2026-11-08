# Azure Data Explorer setup for KQL practice

> **Purpose:** Environment setup + `SigninLogs` ingestion  
> **Outcome:** Local, Sentinel-like KQL practice environment

> [!TIP]
> This lab uses a simplified `SigninLogs` sample. Once you're comfortable, graduate to the
> [Sentinel Table Library](../tables/README.md) — **27 schema-true tables** with a correlated
> [attack scenario](../tables/scenarios/operation-quiet-ledger/README.md). Generate ready-to-run
> ADX ingest for any of them with `csv_to_kql.py` (see the
> [Azure Sentinel Hunter skill](../../.claude/skills/azure-sentinel-hunter/SKILL.md)).

---

## 🎯 Lab Objective

This lab demonstrates how to practice **Microsoft Sentinel–style KQL**
*without requiring a Sentinel workspace*.

We use **Azure Data Explorer (ADX)** because it speaks the same Kusto Query Language as Microsoft Sentinel,
Log Analytics and Defender XDR advanced hunting, and its free cluster costs nothing.

Not everything carries over: ADX has no Sentinel-specific features such as ASIM parsers, watchlists
(`_GetWatchlist`), Sentinel's built-in functions or the workspace's own tables. Queries that use those need a
real workspace.

---

## ❓ Why Azure Data Explorer (ADX)?

- A free cluster: no Azure subscription or credit card  
- No ingestion costs for practice data  
- The same KQL language for querying  
- Safe to experiment: nothing touches a production workspace  

---

## 📋 Prerequisites

- Microsoft account (free)  
- GitHub access to this repository  

---

## 🧪 Step 1 – Create a Free ADX Cluster

1. Go to https://dataexplorer.azure.com  
2. Sign in with your Microsoft account  
3. Create a **free cluster**. It creates a database for you; use that database for this lab.  
   Reference: [Create a free cluster](https://learn.microsoft.com/en-us/azure/data-explorer/start-for-free-web-ui)  

---

## 🧱 Step 2 – Create the `SigninLogs` Table

> Tables **must exist before ingestion** when using `.ingest`.

```kql
.create table SigninLogs (
    TimeGenerated: datetime,
    UserPrincipalName: string,
    UserDisplayName: string,
    UserId: string,
    AppDisplayName: string,
    AppId: string,
    ClientAppUsed: string,
    IPAddress: string,
    Location: string,
    CorrelationId: string,
    ResultType: string,
    ResultDescription: string,
    RiskLevelAggregated: string,
    RiskState: string,
    AuthenticationRequirement: string,
    AuthenticationMethodsUsed: string,
    TokenIssuerType: string,
    ResourceDisplayName: string,
    IsInteractive: bool,
    ConditionalAccessStatus: string,
    DeviceDetail: dynamic,
    Status: dynamic,
    Type: string
)
```

---

## 📥 Step 3 – Ingest Sample Data from GitHub

```kql
.ingest into table SigninLogs
(
  @"https://raw.githubusercontent.com/iamkaushiksaha/azure-security/main/sentinel/sampledata/SigninLogs_sample_important_columns_110rows.csv"
)
with (format="csv", ignoreFirstRecord=true)
```

---

## ✅ Step 4 – Validate Ingestion

Run the following queries to confirm data ingestion:

```kql
SigninLogs
| count
```

```kql
SigninLogs
| take 10
```

---

## 🧠 Step 5 – First Practice Queries

### Failed Sign-ins

```kql
SigninLogs
| where ResultType != "0"
| summarize FailedCount = count() by UserPrincipalName
| sort by FailedCount desc
```

---

### Risky Sign-ins

```kql
SigninLogs
| where RiskLevelAggregated in ("medium", "high")
| summarize count() by UserPrincipalName
```

---

## 🚫 Troubleshooting

### No Data Returned
- Wait 1–2 minutes after ingestion  
- Verify table name spelling  
- Confirm CSV headers match table schema  

### Permission Errors
- Ensure you are **Database Admin** on the ADX database  

---

## 🎉 Outcome

You now have:

- A safe KQL lab environment  
- Sentinel-like `SigninLogs` data  
- A reusable setup for:
  - Threat hunting  
  - Detection development  
  - Query experimentation  

---

## 🚀 What’s Next

- Load more tables with the [table scripts](adx-table-scripts.md).
- Learn the language step by step in the [KQL reference course](../kql/README.md), starting at Stage 01.
- Practise on all 27 tables and the correlated attack scenario in the [table library](../tables/README.md).
