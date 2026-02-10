# Lab02 – Azure Data Explorer (ADX) Setup for KQL Practice

> **Purpose:** Environment setup + `SigninLogs` ingestion  
> **Outcome:** Local, Sentinel-like KQL practice environment

---

## 🎯 Lab Objective

This lab demonstrates how to practice **Microsoft Sentinel–style KQL**
*without requiring a Sentinel workspace*.

We use **Azure Data Explorer (ADX)** because it runs the **same KQL engine**
used by:

- Microsoft Sentinel  
- Log Analytics  
- Microsoft Defender  

This provides a **safe, free, and cost-effective** learning environment.

---

## ❓ Why Azure Data Explorer (ADX)?

- Free tier available  
- No security data ingestion costs  
- Full KQL language support  
- Ideal for experimentation and learning  

---

## 📋 Prerequisites

- Microsoft account (free)  
- GitHub access to this repository  

---

## 🧪 Step 1 – Create a Free ADX Cluster

1. Go to https://dataexplorer.azure.com  
2. Sign in with your Microsoft account  
3. Create a **Free cluster**  
4. Create a database  
   - Example name: `SentinelLabs`  

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

Proceed to **Lab03** to start writing structured hunting queries
and applying detection logic.
