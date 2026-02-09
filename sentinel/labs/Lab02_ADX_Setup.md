# 🧪 Lab02 – Azure Data Explorer (ADX) Setup for KQL Practice

**Difficulty:** Beginner  
**Estimated time:** 30–45 minutes  
**Prerequisites:** Azure account (Free tier is sufficient)

---

## 🎯 Lab Objective

Set up a **KQL practice environment** using **Azure Data Explorer (ADX)** and Sentinel-style sample data hosted in this GitHub repository.

This lab helps you practice KQL safely **without deploying Microsoft Sentinel**.

---

## 💡 Why Azure Data Explorer?

Azure Data Explorer uses the **same KQL engine** as:

- Microsoft Sentinel  
- Azure Monitor Logs  
- Microsoft Defender XDR  

This makes ADX the perfect environment to learn KQL fundamentals.

---

## 🧱 Architecture Overview

```text
GitHub (CSV sample logs)
        ↓
Azure Data Explorer (ADX)
        ↓
KQL Queries
        ↓
Sentinel-style Analysis & Hunting
```

---

## 📁 Sample Data Used

All sample datasets are available in this repository:

```text
sentinel/sampledata/
```

### Data Mapping

| CSV File | ADX Table | Description |
|---|---|---|
| SigninLogs_sample.csv | SigninLogs | Entra ID sign-in activity |
| AuditLogs_sample.csv | AuditLogs | Directory configuration changes |
| SecurityEvent_sample.csv | SecurityEvent | Windows security events |
| AzureActivity_sample.csv | AzureActivity | Azure control-plane actions |
| OfficeActivity_sample.csv | OfficeActivity | Microsoft 365 user activity |

---

## 🆓 Step 1 – Create an Azure Data Explorer Cluster

1. Open the **Azure Portal**
2. Search for **Azure Data Explorer**
3. Click **Create**

### Recommended settings

- **Cluster name:** `sentinel-labs-cluster`
- **Region:** Any nearby region
- **Pricing tier:** **Dev/Test (Free)**

> The free tier is sufficient for all labs in this repository.

---

## 🗄️ Step 2 – Create a Database

Inside the ADX cluster:

1. Go to **Databases**
2. Click **Create database**

**Database name:** `SentinelLabs`  
**Retention:** Default

---

## 📊 Step 3 – Create Sentinel-Style Tables

Open the **Query** blade and run the following commands.

### Create `SigninLogs`

```kql
.create table SigninLogs (
    TimeGenerated: datetime,
    UserPrincipalName: string,
    AppDisplayName: string,
    IPAddress: string,
    Location: string,
    ResultType: string,
    ResultDescription: string
)
```

### Create `AuditLogs`

```kql
.create table AuditLogs (
    TimeGenerated: datetime,
    OperationName: string,
    InitiatedBy: string,
    TargetResources: string,
    Result: string
)
```

### Create `SecurityEvent`

```kql
.create table SecurityEvent (
    TimeGenerated: datetime,
    Computer: string,
    EventID: int,
    Account: string,
    Activity: string
)
```

### Create `AzureActivity`

```kql
.create table AzureActivity (
    TimeGenerated: datetime,
    OperationName: string,
    Caller: string,
    ResourceGroup: string,
    ActivityStatus: string
)
```

### Create `OfficeActivity`

```kql
.create table OfficeActivity (
    TimeGenerated: datetime,
    UserId: string,
    Operation: string,
    Workload: string,
    ClientIP: string
)
```

---

## ⬇️ Step 4 – Ingest CSV Data from GitHub

Data is ingested **directly from GitHub raw URLs**, making this lab fully reproducible.

### Ingest `SigninLogs`

```kql
.ingest into table SigninLogs
(@"https://raw.githubusercontent.com/iamkaushiksaha/azure-security/main/sentinel/sampledata/SigninLogs_sample.csv")
with (format="csv", ignoreFirstRecord=true)
```

### Ingest `AuditLogs`

```kql
.ingest into table AuditLogs
(@"https://raw.githubusercontent.com/iamkaushiksaha/azure-security/main/sentinel/sampledata/AuditLogs_sample.csv")
with (format="csv", ignoreFirstRecord=true)
```

### Ingest remaining tables

Repeat the same pattern for:

- `SecurityEvent`  
  `https://raw.githubusercontent.com/iamkaushiksaha/azure-security/main/sentinel/sampledata/SecurityEvent_sample.csv`
- `AzureActivity`  
  `https://raw.githubusercontent.com/iamkaushiksaha/azure-security/main/sentinel/sampledata/AzureActivity_sample.csv`
- `OfficeActivity`  
  `https://raw.githubusercontent.com/iamkaushiksaha/azure-security/main/sentinel/sampledata/OfficeActivity_sample.csv`

---

## ✅ Step 5 – Validate Ingestion

### Record count

```kql
SigninLogs
| count
```

### Preview data

```kql
SigninLogs
| take 10
```

If rows are returned, ingestion was successful.

---

## 🕵️ Step 6 – First KQL Practice Queries

### Failed sign-ins

```kql
SigninLogs
| where ResultType != "0"
| summarize FailedAttempts = count() by UserPrincipalName
| sort by FailedAttempts desc
```

### Top IP addresses

```kql
SigninLogs
| where ResultType != "0"
| summarize Attempts = count() by IPAddress
| sort by Attempts desc
```

### Azure activity summary

```kql
AzureActivity
| summarize count() by OperationName
| sort by count_ desc
```

---

## 🛠️ Troubleshooting

### No data returned

- Wait 1–2 minutes after ingestion
- Verify table names
- Check CSV header matches schema

### Ingestion failure

- Verify GitHub raw URL is accessible
- Re-run the `.ingest` command

### Permission issues

- Ensure you are **Database Admin** on the ADX cluster

---

## 🧠 What You Learned

- How Sentinel-style logs are structured  
- How KQL behaves on real datasets  
- How ingestion pipelines work  
- How analysts validate and explore logs  

---

## 🚀 What’s Next

- **Lab01 – KQL Foundations**
- **Lab03 – KQL Hunting Queries (MITRE-mapped)**

You now have a **solid KQL practice environment**.

