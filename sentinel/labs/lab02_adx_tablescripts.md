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
    Workload: string,
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
