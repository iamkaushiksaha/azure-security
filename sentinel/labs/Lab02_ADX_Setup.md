🧪 Lab02 – Azure Data Explorer (ADX) Setup for KQL Practice

Difficulty: Beginner
Estimated time: 30–45 minutes
Prerequisites: Azure account (Free tier is sufficient)
Goal: Set up a KQL practice environment using Azure Data Explorer and Sentinel-style sample data hosted on GitHub.

🎯 Why this lab exists

Before writing detection rules or hunting queries in Microsoft Sentinel, you must first understand Kusto Query Language (KQL) and how it behaves on real data.

Azure Data Explorer (ADX) is the same KQL engine that powers:

Microsoft Sentinel

Log Analytics

Microsoft Defender XDR

This lab allows you to:

Practice KQL without deploying Sentinel

Ingest realistic log data

Experiment safely

Learn faster, with zero production risk

Think of ADX as a KQL sandbox.

🧱 Architecture Overview
GitHub (CSV sample logs)
        ↓
Azure Data Explorer (ADX)
        ↓
KQL Queries
        ↓
Sentinel-style Analysis & Hunting


You will ingest CSV files hosted in this GitHub repository directly into ADX tables and query them using KQL.

📁 Sample Data Used in This Lab

All sample data is stored in this repository:

sentinel/sampledata/

Data mapping
CSV File	ADX Table	Represents
SigninLogs_sample.csv	SigninLogs	Entra ID sign-in events
AuditLogs_sample.csv	AuditLogs	Directory & configuration changes
SecurityEvent_sample.csv	SecurityEvent	Windows security events
AzureActivity_sample.csv	AzureActivity	Azure control-plane activity
OfficeActivity_sample.csv	OfficeActivity	Microsoft 365 user activity

These datasets are simplified but realistic, designed specifically for learning.

🆓 Step 1 – Create an Azure Data Explorer Cluster

Open Azure Portal

Search for Azure Data Explorer

Click Create

Recommended values

Cluster name: sentinel-labs-cluster

Region: Any nearby region

Pricing tier: Dev/Test (Free)

⚠️ The free tier is sufficient for all labs in this repository.

Once deployed, open the cluster.

🗄️ Step 2 – Create a Database

Inside the ADX cluster:

Click Databases

Click Create database

Database settings

Database name: SentinelLabs

Retention: Default

Cache: Default

This database will host all lab tables.

📊 Step 3 – Create Sentinel-Style Tables

Open the Query blade in ADX and run the following commands.

Create SigninLogs table
.create table SigninLogs (
    TimeGenerated: datetime,
    UserPrincipalName: string,
    AppDisplayName: string,
    IPAddress: string,
    Location: string,
    ResultType: string,
    ResultDescription: string
)

Create AuditLogs table
.create table AuditLogs (
    TimeGenerated: datetime,
    OperationName: string,
    InitiatedBy: string,
    TargetResources: string,
    Result: string
)

Create SecurityEvent table
.create table SecurityEvent (
    TimeGenerated: datetime,
    Computer: string,
    EventID: int,
    Account: string,
    Activity: string
)

Create AzureActivity table
.create table AzureActivity (
    TimeGenerated: datetime,
    OperationName: string,
    Caller: string,
    ResourceGroup: string,
    ActivityStatus: string
)

Create OfficeActivity table
.create table OfficeActivity (
    TimeGenerated: datetime,
    UserId: string,
    Operation: string,
    Workload: string,
    ClientIP: string
)

⬇️ Step 4 – Ingest CSV Data from GitHub

We will ingest data directly from GitHub raw URLs.

This ensures the lab is fully reproducible for anyone following your blog or repo.

Ingest SigninLogs
.ingest into table SigninLogs
(@"https://raw.githubusercontent.com/iamkaushiksaha/azure-security/main/sentinel/sampledata/SigninLogs_sample.csv")
with (format="csv", ignoreFirstRecord=true)

Ingest AuditLogs
.ingest into table AuditLogs
(@"https://raw.githubusercontent.com/iamkaushiksaha/azure-security/main/sentinel/sampledata/AuditLogs_sample.csv")
with (format="csv", ignoreFirstRecord=true)

Ingest remaining tables

Repeat the same pattern for:

SecurityEvent_sample.csv

AzureActivity_sample.csv

OfficeActivity_sample.csv

✅ Step 5 – Validate Data Ingestion

Run these checks to confirm ingestion.

Record count check
SigninLogs
| count

Preview data
SigninLogs
| take 10


If rows are returned, ingestion is successful.

Repeat for other tables.

🧠 Step 6 – Your First Real KQL Queries
Failed sign-in analysis
SigninLogs
| where ResultType != "0"
| summarize FailedAttempts = count() by UserPrincipalName
| sort by FailedAttempts desc

Top attacking IP addresses
SigninLogs
| where ResultType != "0"
| summarize Attempts = count() by IPAddress
| sort by Attempts desc

Azure activity monitoring
AzureActivity
| summarize count() by OperationName
| sort by count_ desc

🛠️ Troubleshooting
❌ No data returned

Wait 1–2 minutes after ingestion

Verify table name spelling

Confirm CSV headers match schema

❌ Ingestion command fails

Ensure raw GitHub URL opens in browser

Check CSV file is not empty

Re-run .ingest command

❌ Permission denied

Ensure your user is Database Admin on the ADX cluster

🧠 What You Learned in This Lab

By completing this lab, you now understand:

How Sentinel-style logs are structured

How KQL operates on real data

How ingestion pipelines work

How analysts validate and explore logs

This is the exact foundation required for:

Threat hunting

Detection engineering

Analytics rule creation

Workbooks and dashboards
