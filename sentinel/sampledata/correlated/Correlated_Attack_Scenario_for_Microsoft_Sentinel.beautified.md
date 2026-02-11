# Correlated Attack Scenario for Microsoft Sentinel

![MITRE
ATT&CK](https://img.shields.io/badge/MITRE%20ATT%26CK-Mapped-red)
![Microsoft
Sentinel](https://img.shields.io/badge/Microsoft%20Sentinel-Correlation%20Dataset-blue)
![Azure](https://img.shields.io/badge/Azure-Security-0078D4)
![KQL](https://img.shields.io/badge/KQL-Queries-informational)

------------------------------------------------------------------------

## Overview

This dataset simulates a **multi-stage attack** unfolding over a fixed
timeline. Each session represents an adversary who:

-   Brute-forces an account\
-   Signs in with valid credentials\
-   Escalates privileges\
-   Moves laterally via **RDP**\
-   Executes malicious **PowerShell**\
-   Performs internal network scanning\
-   Triggers **Microsoft Sentinel** alerts and incidents

Each session is linked end-to-end using a shared `CorrelationId` across
tables.

------------------------------------------------------------------------

## Included Tables

Nine correlated tables are designed to be ingested into **Microsoft
Sentinel** (or any Kusto-based environment):

-   `SigninLogs_correlated.csv`
-   `AuditLogs_correlated.csv`
-   `SecurityEvent_correlated.csv`
-   `Syslog_correlated.csv`
-   `CommonSecurityLog_correlated.csv`
-   `AzureActivity_correlated.csv`
-   `OfficeActivity_correlated.csv`
-   `SecurityAlert_correlated.csv`
-   `SecurityIncident_correlated.csv`

> Each table typically contains **50--200 rows** per file across **10
> attack sessions**.

------------------------------------------------------------------------

## Attack Timeline (T0--T56+)

``` mermaid
flowchart TD
  T0["T0–T10\nFailed sign-ins\nBrute Force (T1110)"] --> T11["T11\nSuccessful sign-in\nValid Accounts (T1078)"]
  T11 --> T12["T12–T20\nPrivilege change\nAccount Manipulation (T1098)"]
  T12 --> T21["T21–T40\nRDP + PowerShell\nRemote Services (T1021)\nPowerShell (T1059.001)"]
  T21 --> T25["T25–T45\nNetwork scanning / firewall traffic\nNetwork Service Scanning (T1046)"]
  T25 --> T46["T46–T55\nAlerts generated\nSentinel Analytics"]
  T46 --> T56["T56+\nIncident creation\nSentinel Incidents"]
```

------------------------------------------------------------------------

## Visual Attack Flow

``` mermaid
flowchart LR
  A["Brute Force\nT1110"] --> B["Valid Sign-in\nT1078"]
  B --> C["Account Manipulation\nT1098"]
  C --> D["RDP Lateral Movement\nT1021"]
  D --> E["PowerShell Execution\nT1059.001"]
  E --> F["Network Service Scanning\nT1046"]
  F --> G["Alerts\nSecurityAlert_correlated"]
  G --> H["Incidents\nSecurityIncident_correlated"]
```

------------------------------------------------------------------------

## Shared Correlation Anchors

  Field                  Purpose
  ---------------------- ---------------------------------------------
  TimeGenerated          Aligns events chronologically (UTC).
  UserPrincipalName      Cloud identity (e.g., user1@contoso.com).
  AccountName            On-premises account name (e.g., user1).
  IPAddress / SourceIP   Network origin of activity.
  Computer               Hostname of the affected system.
  CorrelationId          Session identifier linking attack events.
  AlertId → IncidentId   Alerts mapped to incidents via correlation.

------------------------------------------------------------------------

## MITRE ATT&CK Mapping

  ---------------------------------------------------------------------------------
  Phase         Technique            ID          Primary Tables
  ------------- -------------------- ----------- ----------------------------------
  Credential    Brute Force          T1110       SigninLogs_correlated.csv
  Access                                         

  Initial       Valid Accounts       T1078       SigninLogs_correlated.csv
  Access                                         

  Privilege     Account Manipulation T1098       AuditLogs_correlated.csv
  Escalation                                     

  Lateral       Remote Services      T1021       SecurityEvent_correlated.csv
  Movement                                       

  Execution     PowerShell           T1059.001   Syslog_correlated.csv

  Discovery     Network Service      T1046       CommonSecurityLog_correlated.csv
                Scanning                         

  Detection     Sentinel Analytics   N/A         SecurityAlert_correlated.csv

  Incident      Case Management      N/A         SecurityIncident_correlated.csv
  ---------------------------------------------------------------------------------

------------------------------------------------------------------------

## Sample KQL Queries

### Identify All Events for a Session

``` kql
let targetCorrelationId = 'session_01';
union SigninLogs_correlated, AuditLogs_correlated, SecurityEvent_correlated, Syslog_correlated,
      CommonSecurityLog_correlated, AzureActivity_correlated, OfficeActivity_correlated,
      SecurityAlert_correlated, SecurityIncident_correlated
| where CorrelationId == targetCorrelationId
| sort by TimeGenerated asc
```

### Failed Sign-ins Followed by Success

``` kql
SigninLogs_correlated
| summarize FailedCount = countif(Status == 'Failure'), 
          SuccessTime = maxif(TimeGenerated, Status == 'Success')
  by CorrelationId
| where FailedCount > 0
```

### Detect Privilege Escalation After Login

``` kql
let successfulSessions = SigninLogs_correlated
    | where Status == 'Success'
    | summarize min(TimeGenerated) by CorrelationId;
AuditLogs_correlated
| join kind=inner successfulSessions on CorrelationId
| where TimeGenerated > min_TimeGenerated
| project TimeGenerated, CorrelationId, OperationName, TargetRole
```

### Link Alerts to Incidents

``` kql
SecurityAlert_correlated
| join kind=inner SecurityIncident_correlated on IncidentId
| sort by TimeGenerated asc
| project TimeGenerated, AlertName, TechniqueId, TechniqueName, IncidentId, Title
```

------------------------------------------------------------------------

## References

-   MITRE ATT&CK: https://attack.mitre.org/
-   Azure Monitor SigninLogs Reference:
    https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/signinlogs

------------------------------------------------------------------------

> This dataset contains synthetic data for detection engineering
> practice and does not represent real user activity.
