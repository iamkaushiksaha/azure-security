# KQL Basics  
### A Practical Foundation for Microsoft Sentinel Analysts

> **Audience:** SOC Tier 1–2 Analysts, Threat Hunters, Detection Engineers  
> **Goal:** Learn how to *think* in KQL — not just copy queries

---

## 🎯 Why This Module Exists

Kusto Query Language (**KQL**) is the backbone of **Microsoft Sentinel**, **Azure Monitor**, and **Microsoft Defender** analytics.

Many analysts struggle not because KQL is complex —  
but because they approach it as **syntax**, not **logic**.

This guide helps you:

- Build a strong **mental model** for KQL  
- Understand how Sentinel data behaves at scale  
- Write queries that are **efficient, readable, and reusable**  

---

## 📊 Dataset Used Throughout This Guide

We use **`SigninLogs`** as the primary dataset because it is:

- One of the most security-critical Sentinel tables  
- Rich in identity, network, application, and risk signals  
- Reusable across hunting, detections, and investigations  

> Mastering `SigninLogs` makes every other Sentinel table easier.

---

## 🔍 What Is KQL?

KQL is a **read-only query language** designed for **high-volume telemetry**.

It is optimized for:

- Log analytics  
- Threat hunting  
- Telemetry exploration  
- Security investigations  

Used across:

- Microsoft Sentinel  
- Azure Data Explorer (ADX)  
- Log Analytics  
- Microsoft Defender  

---

## 🧠 How to Think in KQL (Mental Model)

KQL queries execute **left → right**.  
Each line transforms the output of the previous one.

```text
Table
| Filter
| Transform
| Aggregate
| Sort / Project
```

### Example: Reading a Query Like a Sentence

```kql
SigninLogs
| where ResultType != "0"
| summarize FailedAttempts = count() by UserPrincipalName
| sort by FailedAttempts desc
```

---

## 🧩 Core Operators Every Analyst Must Know

| Operator | Why It Matters |
|--------|---------------|
| `where` | Reduce noise early |
| `project` | Improve readability |
| `extend` | Add calculated logic |
| `summarize` | Reveal patterns |
| `count()` | Measure activity |
| `sort by` | Prioritize results |
| `parse_json()` | Extract dynamic data |
| `tostring()` | Normalize types |
| `distinct` | Identify uniqueness |
| `take` | Safely explore data |

---

## 🧱 Key Columns from `SigninLogs`

| Column | Why It Matters |
|------|---------------|
| `TimeGenerated` | Timeline reconstruction |
| `UserPrincipalName` | Identity tracking |
| `IPAddress` | Network analysis |
| `AppDisplayName` | Application abuse |
| `ClientAppUsed` | Legacy auth risk |
| `Location` | Geo anomalies |
| `ResultType` | Success vs failure |
| `ResultDescription` | Failure context |
| `CorrelationId` | Session tracing |
| `RiskLevelAggregated` | Identity risk |

---

## ⏱️ Time Filtering & Query Hygiene

Every investigation should start with **time**.

```kql
SigninLogs
| where TimeGenerated > ago(24h)
```

> ⚠️ Missing time filters often leads to slow or misleading queries.

---

## 🚫 Common Beginner Mistakes

- Filtering before understanding columns  
- Forgetting `TimeGenerated`  
- Using `project *` on large datasets  
- Copy-pasting queries blindly  

---

## ✅ Best Practice: Start Like This

```kql
SigninLogs
| take 10
```

This helps you understand schema, values, and behavior safely.

---

## 🧭 Recommended Query Development Flow

```text
Table
| take 10
| where TimeGenerated > ago(24h)
| where <condition>
| summarize <aggregation>
| sort by <field>
```

---

## 🧪 Practical Examples

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

## 🚀 What Comes Next

- Lab02 – Azure Data Explorer setup  
- MITRE-mapped hunting queries  
- Detection rule engineering  
- Cross-table correlation  

---

> **Status:** Enterprise-ready • Training-grade • GitHub compatible
