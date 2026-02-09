👉 Purpose: Teach how to think in KQL, not just syntax
👉 Audience: SOC L1/L2, Sentinel beginners, career switchers

📘 KQL Basics for Microsoft Sentinel (Beginner-Friendly)
Why this lab exists

Most people learn KQL by copy-pasting queries.
That works… until something breaks.

This guide focuses on:

Understanding how KQL thinks

Building queries step by step

Preparing you for real Sentinel investigations

This is the foundation for all Sentinel hunting, analytics rules, and workbooks.

🧠 How to think in KQL (mental model)

KQL always follows this flow:

Table
→ Filter rows
→ Shape columns
→ Aggregate (optional)
→ Sort / visualize


Example:

SigninLogs
| where ResultType != "0"
| summarize count() by UserPrincipalName
| sort by count_ desc

📦 Common Sentinel Tables you’ll practice on

In this lab, we’ll simulate these Sentinel tables using CSV data:

Table Name	What it represents
SigninLogs	Azure AD sign-ins
AuditLogs	Azure AD changes
SecurityEvent	Windows security logs
SecurityAlert	Defender alerts
SecurityIncident	Sentinel incidents
🔑 Essential KQL operators (you MUST know these)
take

Quickly preview data.

SigninLogs
| take 10

where

Filter rows (this is 80% of KQL).

SigninLogs
| where ResultType != "0"

project

Select only useful columns.

SigninLogs
| project TimeGenerated, UserPrincipalName, IPAddress

extend

Create calculated fields.

SigninLogs
| extend IsFailure = ResultType != "0"

summarize

Aggregate data (counts, trends).

SigninLogs
| summarize FailedLogins = count() by UserPrincipalName

sort by

Rank results.

SigninLogs
| summarize count() by IPAddress
| sort by count_ desc

⏱️ Time filtering (very important)

Most Sentinel tables use TimeGenerated.

SigninLogs
| where TimeGenerated > ago(24h)


⚠️ Forgetting time filters is one of the most common mistakes.

🚫 Beginner mistakes to avoid

❌ Filtering before checking column names
❌ Forgetting TimeGenerated
❌ Using project *
❌ Copy-pasting without understanding

✅ Always start with:

TableName
| take 10

🎯 What’s next?

Once you understand these basics, you’re ready to:

Load real data

Practice on realistic logs

Build detection logic

➡️ Continue to Lab02 – ADX Setup to load Sentinel-like data and practice KQL hands-on.
