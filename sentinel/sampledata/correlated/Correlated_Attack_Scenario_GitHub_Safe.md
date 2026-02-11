# Correlated Attack Scenario for Microsoft Sentinel

![MITRE
ATT&CK](https://img.shields.io/badge/MITRE%20ATT%26CK-Mapped-red)
![Microsoft
Sentinel](https://img.shields.io/badge/Microsoft%20Sentinel-Correlation%20Dataset-blue)
![Azure](https://img.shields.io/badge/Azure-Security-0078D4)
![KQL](https://img.shields.io/badge/KQL-Queries-informational)

## Overview

This dataset simulates a multi-stage attack unfolding over a fixed
timeline. Each session represents an adversary who:

-   Brute-forces an account
-   Signs in with valid credentials
-   Escalates privileges
-   Moves laterally via RDP
-   Executes malicious PowerShell
-   Performs internal network scanning
-   Triggers Microsoft Sentinel alerts and incidents

Each session is linked end-to-end using a shared `CorrelationId` across
tables.

## Included Tables

Nine correlated tables are designed to be ingested into Microsoft
Sentinel (or any Kusto-based environment):

-   `SigninLogs_correlated.csv`
-   `AuditLogs_correlated.csv`
-   `SecurityEvent_correlated.csv`
-   `Syslog_correlated.csv`
-   `CommonSecurityLog_correlated.csv`
-   `AzureActivity_correlated.csv`
-   `OfficeActivity_correlated.csv`
-   `SecurityAlert_correlated.csv`
-   `SecurityIncident_correlated.csv`

Each table typically contains 50-200 rows per file across 10 attack
sessions.

## Shared Correlation Anchors

  -----------------------------------------------------------------------
  Field                               Purpose
  ----------------------------------- -----------------------------------
  TimeGenerated                       Aligns events chronologically;
                                      recorded in UTC.

  UserPrincipalName                   Cloud identity (e.g.,
                                      user1@contoso.com).

  AccountName                         On-premises account name used in
                                      security events.

  IPAddress / SourceIP                Network origin of the activity.

  Computer                            Hostname of the system on which the
                                      event occurred.

  CorrelationId                       Session identifier linking all
                                      related events.

  AlertId -\> IncidentId              Links alerts to incidents for case
                                      management.
  -----------------------------------------------------------------------

## MITRE ATT&CK Mapping

  ----------------------------------------------------------------------------------------
  Phase             Technique         ID                Primary Tables
  ----------------- ----------------- ----------------- ----------------------------------
  Credential Access Brute Force       T1110             SigninLogs_correlated.csv

  Initial Access    Valid Accounts    T1078             SigninLogs_correlated.csv

  Privilege         Account           T1098             AuditLogs_correlated.csv
  Escalation        Manipulation                        

  Lateral Movement  Remote Services   T1021             SecurityEvent_correlated.csv

  Execution         PowerShell        T1059.001         Syslog_correlated.csv

  Discovery         Network Service   T1046             CommonSecurityLog_correlated.csv
                    Scanning                            

  Detection         Sentinel          N/A               SecurityAlert_correlated.csv
                    Analytics                           

  Incident          Case Management   N/A               SecurityIncident_correlated.csv
  ----------------------------------------------------------------------------------------

## Sample Kusto Query

``` kusto
let targetCorrelationId = 'session_01';
union SigninLogs_correlated, AuditLogs_correlated, SecurityEvent_correlated, Syslog_correlated,
      CommonSecurityLog_correlated, AzureActivity_correlated, OfficeActivity_correlated,
      SecurityAlert_correlated, SecurityIncident_correlated
| where CorrelationId == targetCorrelationId
| sort by TimeGenerated asc
```

## References

-   https://attack.mitre.org/techniques/T1110/
-   https://attack.mitre.org/techniques/T1078/
-   https://attack.mitre.org/techniques/T1098/
-   https://attack.mitre.org/techniques/T1021/
-   https://attack.mitre.org/techniques/T1059/001/
-   https://attack.mitre.org/techniques/T1046/
-   https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/signinlogs
