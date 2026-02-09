# KQL Basics – Foundation for Microsoft Sentinel

This guide introduces **Kusto Query Language (KQL)** from a security analyst’s perspective.  
Instead of memorizing syntax, you will learn **how to think in KQL** using realistic Microsoft Sentinel data.

This module uses **`SigninLogs`** as the primary dataset because it is:

- One of the most critical Microsoft Sentinel tables  
- Rich in identity, network, application, and risk signals  
- Reusable for hunting, detections, and investigations  

---

## What is KQL?

KQL is a **read-only query language** optimized for:

- Log analytics  
- Threat hunting  
- Telemetry exploration  
- Security investigations  

It is used across:

- Microsoft Sentinel  
- Azure Data Explorer (ADX)  
- Log Analytics  
- Microsoft Defender  

---

## How to Think in KQL (Mental Model)

KQL queries always flow **left → right**:

```kql
Table
| Filter
| Transform
| Aggregate
| Sort / Project
```

### Example Query Flow

```kql
SigninLogs
| where ResultType != "0"
| summarize FailedAttempts = count() by UserPrincipalName
| sort by FailedAttempts desc
```

---

## Core Operators Every Analyst Must Know

| Operator | Purpose |
|--------|--------|
| `where` | Filter rows |
| `project` | Select columns |
| `extend` | Create calculated fields |
| `summarize` | Aggregate data |
| `count()` | Event counting |
| `sort by` | Ordering |
| `parse_json()` | Parse dynamic fields |
| `tostring()` | Convert data types |
| `distinct` | Return unique values |
| `take` | Preview rows |

---

## Key Columns from `SigninLogs` (Used Throughout Labs)

| Column | Why It Matters |
|------|---------------|
| `TimeGenerated` | Timeline analysis |
| `UserPrincipalName` | Identity tracking |
| `IPAddress` | Network analysis |
| `AppDisplayName` | Application abuse detection |
| `ClientAppUsed` | Legacy authentication risk |
| `Location` | Geographic anomaly detection |
| `ResultType` | Success vs failure |
| `ResultDescription` | Failure reason |
| `CorrelationId` | Session tracing |
| `RiskLevelAggregated` | Identity risk assessment |

---

## ⏱️ Time Filtering & Query Hygiene (Read This Carefully)

Most Microsoft Sentinel and Log Analytics tables are **time-series datasets**.  
Almost every investigation starts with **time**.

The standard column used for time filtering is:

```kql
TimeGenerated
```

### Basic Time Filter Example

```kql
SigninLogs
| where TimeGenerated > ago(24h)
```

> ⚠️ Forgetting time filters is one of the most common beginner mistakes and can result in slow queries or misleading results.

---

## 🚫 Common Beginner Mistakes to Avoid

❌ Filtering before checking column names  
❌ Forgetting `TimeGenerated`  
❌ Using `project *` on large datasets  
❌ Copy-pasting queries without understanding the logic  

---

## ✅ Best Practice: Always Start Like This

```kql
SigninLogs
| take 10
```

This helps you:
- Understand available columns  
- Inspect real values  
- Avoid syntax errors  
- Write cleaner and faster queries  

---

## 🧭 Recommended Query Flow

```kql
Table
| take 10
| where TimeGenerated > ago(24h)
| where <condition>
| summarize <aggregation>
| sort by <field>
```

---

## Example Queries

### Failed Sign-ins by User

```kql
SigninLogs
| where ResultType != "0"
| summarize Failed = count() by UserPrincipalName
| sort by Failed desc
```

### Suspicious IP Addresses

```kql
SigninLogs
| where ResultType != "0"
| summarize Attempts = count() by IPAddress
| sort by Attempts desc
```

### Legacy Authentication Usage

```kql
SigninLogs
| where ClientAppUsed !in ("Browser", "Mobile Apps and Desktop clients")
| summarize count() by ClientAppUsed
```

---

## What Comes Next?

- **Lab02** – Setting up Azure Data Explorer  
- MITRE-mapped hunting queries  
- Detection rule design  
- Cross-table correlation  
