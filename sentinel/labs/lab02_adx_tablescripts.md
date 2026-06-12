# ADX Table Creation & Ingestion Scripts (Reusable)

> **Purpose:** Enterprise-style reusable ADX scripts  
> **Importance:** Critical for scaling labs, joins, and correlations

---

## 🎯 Why This Document Exists

This document contains **reusable Azure Data Explorer (ADX) scripts**
for creating **Sentinel-style tables** and ingesting data.

Use this document when:

- Adding additional Sentinel tables  
- Teaching joins and cross-table correlation  
- Extending labs beyond `SigninLogs`  
- Building reusable KQL practice environments  

---

## 🧱 Table Creation Scripts

Each table below mirrors commonly used Microsoft Sentinel schemas.

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

> [!TIP]
> These are **simplified teaching CSVs**. For **schema-true** data (every column validated against
> Microsoft Learn) across **27 tables** plus a correlated attack scenario, use the
> [Sentinel Table Library](../tables/README.md). To ingest any library table into ADX with a
> correct auto-generated `.create table` + ingest, run the skill's generator instead of writing the
> schema by hand:
> ```bash
> python3 .claude/skills/azure-sentinel-hunter/scripts/csv_to_kql.py \
>     sentinel/tables/AuditLogs/AuditLogs_sample.csv --mode adx
> ```

### Data Mapping

| CSV File | ADX Table | Description |
|---|---|---|
| SigninLogs_sample.csv | SigninLogs | Entra ID sign-in activity |
| AuditLogs_sample.csv | AuditLogs | Directory configuration changes |
| SecurityEvent_sample.csv | SecurityEvent | Windows security events |
| AzureActivity_sample.csv | AzureActivity | Azure control-plane actions |
| OfficeActivity_sample.csv | OfficeActivity | Microsoft 365 user activity |

---

### AuditLogs

```kql
.create table AuditLogs (
    TimeGenerated: datetime,
    OperationName: string,
    InitiatedBy: string,
    TargetResources: string,
    Result: string
)
```

---

### AzureActivity

```kql
.create table AzureActivity (
    TimeGenerated: datetime,
    OperationName: string,
    Caller: string,
    ResourceGroup: string,
    ActivityStatus: string
)
```

---

### OfficeActivity

```kql
.create table OfficeActivity (
    TimeGenerated: datetime,
    UserId: string,
    Operation: string,
    OfficeWorkload: string,
    ClientIP: string
)
```

---

### SecurityEvent

```kql
.create table SecurityEvent (
    TimeGenerated: datetime,
    Computer: string,
    EventID: int,
    Account: string,
    Activity: string
)
```

---

## 📥 Ingestion Template (Reusable)

Use the following ingestion pattern for **any table**:

```kql
.ingest into table <TableName>
(
  @"<RAW_GITHUB_URL>"
)
with (format="csv", ignoreFirstRecord=true)
```

---
Ingest CSV Data from GitHub

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


## ✅ Best Practice Guidance

| Level | Recommendation |
|-----|---------------|
| Beginner | Focus on one table at a time |
| Intermediate | Practice joins between tables |
| Advanced | Build MITRE-aligned correlations |

---

## 📚 Reference (Microsoft Learn)

Use these official references to discover schemas and example queries:

- https://learn.microsoft.com/en-in/azure/azure-monitor/reference/tables-category
- https://learn.microsoft.com/en-in/azure/azure-monitor/reference/queries-by-table

---

## 🚀 What’s Next

Use these tables to:

- Practice multi-table hunting  
- Learn `join` and `lookup` patterns  
- Build detection-ready queries  
- Extend future labs  
