🧪 Lab02 – Setting up Azure Data Explorer (ADX) for KQL Practice
Why ADX?

Azure Data Explorer (ADX) uses the same KQL engine as:

Microsoft Sentinel

Log Analytics

Microsoft Defender

This lab lets you:

Practice KQL without a Sentinel workspace

Learn safely

Experiment freely

🆓 Prerequisites

Azure account (free tier works)

GitHub access to this repo

Browser (no local tools needed)

🔧 Step 1: Create ADX Cluster

Go to Azure Portal

Search for Azure Data Explorer

Create:

Cluster name: sentinel-labs-cluster

Region: any

Pricing: Dev/Test (free)

🗄️ Step 2: Create database

Inside the cluster:

Database name: SentinelLabs

Retention: default

📊 Step 3: Create tables (Sentinel-like schemas)
Example: SigninLogs
.create table SigninLogs (
    TimeGenerated: datetime,
    UserPrincipalName: string,
    AppDisplayName: string,
    IPAddress: string,
    Location: string,
    ResultType: string,
    ResultDescription: string
)


Repeat similar steps for:

AuditLogs

SecurityEvent

SecurityAlert

SecurityIncident

(We intentionally keep schemas simple for learning.)

⬇️ Step 4: Ingest CSV data from GitHub
Example: SigninLogs ingestion
.ingest into table SigninLogs
(@"https://raw.githubusercontent.com/iamkaushiksaha/azure-security/main/sentinel/sampledata/SigninLogs_sample.csv")
with (format="csv", ignoreFirstRecord=true)


Repeat for other tables using their respective raw URLs.

✅ Step 5: Validate ingestion
SigninLogs
| count

SigninLogs
| take 10


If data appears — you’re ready.

🕵️ Step 6: First real KQL queries
Failed sign-ins
SigninLogs
| where ResultType != "0"
| summarize count() by UserPrincipalName
| sort by count_ desc

Top attacking IPs
SigninLogs
| where ResultType != "0"
| summarize count() by IPAddress
| sort by count_ desc

🧠 What you just learned

✔ How Sentinel data is structured
✔ How ingestion works
✔ How KQL behaves on real data
✔ How analysts investigate sign-ins
