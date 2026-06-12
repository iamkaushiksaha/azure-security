# Alert

> **Category:** Azure Monitor (Solution: `LogManagement`)
> **Connector / source:** Azure Monitor alert rules — **metric**, **log search (scheduled query)**, and **Activity Log** alert rules — plus System Center Operations Manager (SCOM) alerts forwarded by the Log Analytics agent / SCOM connector. **Legacy table:** only *older versions of log search alerts* (and SCOM) actually write rows here. Modern Azure Monitor alerts are **not** stored in this table — Microsoft directs you to **Azure Resource Graph** (`alertsmanagementresources`) to query current alerts of any type.
> **Table plan:** Analytics (default). The reference flags **Basic log: No**, **Ingestion-time DCR support: Yes**, **Lake-only ingestion: No**.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/alert

> ⚠️ **This is the Azure Monitor `Alert` table — NOT `SecurityAlert`.**
> `Alert` = **infrastructure / health** alerts fired by Azure Monitor alert *rules* (a CPU metric crossing a threshold, a scheduled KQL query returning rows, an Activity-Log condition matching). `SecurityAlert` = **security detections** from Microsoft Sentinel analytics rules, Microsoft Defender XDR, Defender for Cloud, MDCA, etc. They are different tables with different schemas and different producers. A row in `Alert` means "a monitoring rule fired"; a row in `SecurityAlert` means "a security product thinks this is malicious/suspicious." Do not confuse the two in detections, dashboards, or joins.

## What this table is
Each row is **one Azure Monitor (or SCOM) alert instance** — the firing of a metric / log-search / Activity-Log alert rule — recording the rule (`AlertName`), the severity (`AlertSeverity` / `AlertPriority`), the lifecycle state (`AlertState`), the object it fired on (`SourceDisplayName` / `ResourceId`), and, for threshold and log alerts, the breaching value (`AlertValue` vs `ThresholdOperator` + `ThresholdValue`). For log-search alerts it also carries the `Query`, the evaluation window (`QueryExecutionStartTime` / `QueryExecutionEndTime`) and a `LinkToSearchResults`. Rows appear when a rule transitions to fired, and the same row is updated through its resolution lifecycle (`TimeRaised` → `TimeResolved`, `ResolvedBy`, `RepeatCount`). **Heed the page's warning: this is a *legacy* table** — many tenants see little or nothing here because modern alerts live in the Alerts-management service (query via **Azure Resource Graph**), so treat `Alert` as a *secondary, best-effort* operational signal rather than the system of record. In a SOC its value is **corroboration**: infra/health alerts that fire *during* a security incident (egress spikes, access-spike alerts, Activity-Log alerts on role/key/NSG writes) add an independent, telemetry-derived line of evidence alongside `SecurityAlert`/`SecurityIncident`.

## Schema
Full column list, validated against the Microsoft Learn reference. Types are the KQL/Log Analytics types. This table has **no dynamic columns** — the detail blobs (`AlertContext`, `Query`, etc.) are plain `string`.

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | Date and time the record was created. |
| TimeRaised | datetime | Date and time that the alert was generated (fired). |
| TimeLastModified | datetime | Date and time that the alert was last changed. |
| TimeResolved | datetime | Date and time the alert was resolved. Empty if not yet resolved. |
| AlertId | string | GUID of the alert. |
| AlertName | string | Name of the alert (the alert **rule** name). |
| AlertDescription | string | Detailed description of the alert. |
| AlertContext | string | Details of the data item that caused the alert, in **XML** format. |
| AlertError | string | Error text associated with the alert (if any). |
| AlertPriority | string | Priority level of the alert. |
| PriorityNumber | int | Numeric priority. |
| AlertSeverity | string | Severity level of the alert (e.g. `Sev0`–`Sev4` for Azure Monitor; SCOM uses words). |
| AlertState | string | Latest resolution **state** of the alert (e.g. `New`, `Acknowledged`, `Closed`). |
| AlertStatus | int | Numeric status code. |
| StateType | string | State category. |
| StatusDescription | string | Human-readable status. |
| AlertValue | int | The **observed** value that triggered the alert (compare to `ThresholdValue`). |
| ValueDescription | string | Description of `AlertValue`. |
| ValueFlags | int | Flags qualifying the value. |
| ValueFlagsDescription | string | Description of `ValueFlags`. |
| ThresholdOperator | string | Comparison operator, e.g. `GreaterThan`, `LessThan`, `Equals`. |
| ThresholdValue | int | The configured threshold the rule compares against. |
| Expression | string | The alerting expression (for expression-based rules). |
| Query | string | The KQL query text for a **log search** alert rule. |
| QueryExecutionStartTime | datetime | Start of the query evaluation window. |
| QueryExecutionEndTime | datetime | End of the query evaluation window. |
| LinkToSearchResults | string | Deep link to the log-search results that fired the alert. |
| Url | string | Associated URL. |
| AlertRuleId | string | Identifier of the alert rule. |
| AlertRuleInstanceId | string | Identifier of the specific rule instance/evaluation. |
| AlertTypeNumber | int | Numeric alert type. |
| AlertTypeDescription | string | Description of the alert type. |
| TemplateId | string | Template the alert was created from. |
| TriggerId | string | Identifier of the trigger. |
| RepeatCount | int | Number of times the same alert fired for the same object **since it was last resolved**. |
| Flags | int | Bit flags on the alert. |
| FlagsDescription | string | Description of `Flags`. |
| SourceSystem | string | Agent type that collected the event: `Azure` (Azure Monitor / Azure Diagnostics), `OpsManager` (Windows / SCOM), `Linux` (Linux agents). |
| SourceDisplayName | string | Display name of the monitoring object that generated the alert. |
| SourceFullName | string | Full name of the monitoring object that generated the alert. |
| ObjectDisplayName | string | Display name of the monitored object. |
| RootObjectName | string | Root monitored object name. |
| Computer | string | Computer the alert is associated with (agent-sourced alerts). |
| HostName | string | Host name associated with the alert. |
| ManagementGroupName | string | SCOM management-group name (for Operations Manager agents). |
| ResourceId | string | Resource the alert is associated with (ARM resource id string). |
| _ResourceId | string | Unique identifier for the resource the record is associated with (platform). |
| ResourceType | string | Type of the associated resource. |
| ResourceValue | string | Value/identifier of the resource. |
| _SubscriptionId | string | Unique identifier for the subscription the record is associated with (platform). |
| LastModifiedBy | string | Name of the user who last modified the alert. |
| ResolvedBy | string | Name of the user who resolved the alert. Empty if not yet resolved. |
| Comments | string | Free-text comments on the alert. |
| RepeatCount *(see above)* | int | — |
| RemediationJobId | string | Job id of an automated remediation triggered by the alert. |
| RemediationRunbookName | string | Name of the Automation runbook used for remediation. |
| ServiceDeskId | string | ITSM/service-desk work item id. |
| ServiceDeskConnectionName | string | Name of the ITSM connection. |
| ServiceDeskWorkItemLink | string | Link to the ITSM work item. |
| ServiceDeskWorkItemType | string | Type of ITSM work item. |
| TicketId | string | Ticket id if the SCOM environment is integrated with a ticketing process. Empty if none. |
| Custom1 … Custom10 | string | Ten generic SCOM custom fields carried through from Operations Manager. |
| Type | string | The name of the table (`Alert`). |
| _BilledSize | real | The record size in bytes (platform). |
| _IsBillable | string | Whether ingesting the data is billable; `false` = not billed (platform). |

> **~74 columns** total on the reference (counting `Custom1`–`Custom10` individually). Every detection/triage-relevant column is listed above. Many fields (`Custom*`, `ManagementGroupName`, `RootObjectName`, `Service Desk*`, `Ticket*`, `Remediation*`, `Flags*`) are **SCOM / Operations Manager carry-over** and are typically empty for Azure-Monitor-sourced rows.

## Key columns for detection & hunting
- **Identity:** No actor field for the *firing* of an alert (an alert rule, not a user, fires it). `LastModifiedBy` / `ResolvedBy` capture the **analyst** who handled it (triage attribution), not the adversary. To get the actor behind the *condition*, pivot to the underlying table (`AzureActivity.Caller`, `SigninLogs.UserPrincipalName`, `Syslog`).
- **Host / device:** `Computer` / `HostName` (agent alerts), `SourceDisplayName` / `SourceFullName` / `ObjectDisplayName` (the monitored object), and `ResourceId` / `_ResourceId` (Azure resource).
- **Network:** n/a — no source/dest IP columns. Network detail lives in `AlertContext` (XML) or in the underlying `Query` / source table.
- **Outcome / result:** This table records **that an alert fired**, not a success/failure. Severity is `AlertSeverity` (**string**, e.g. `Sev0`–`Sev4`); lifecycle is `AlertState` (**string**: `New` / `Acknowledged` / `Closed`); the breach is `AlertValue` vs `ThresholdOperator` + `ThresholdValue`.
- **Timestamps:** `TimeRaised` (fired) and `TimeResolved` (resolved); `TimeGenerated` (record created); `QueryExecutionStartTime` / `QueryExecutionEndTime` (the log-alert evaluation window).
- **Join keys (to other tables):** `ResourceId` / `_ResourceId` / `_SubscriptionId` (→ `AzureActivity`, `StorageBlobLogs`, resource diagnostics), `Computer` / `HostName` (→ `SecurityEvent`, `Syslog`, `Heartbeat`, `DeviceEvents`), `TimeRaised` (time-window correlation to `SecurityAlert` / `SecurityIncident`).

## ⚠️ Schema gotchas
- **Legacy table — frequently empty.** The reference states plainly that `Alert` "contains legacy information that is only logged in older versions of log search alerts." Modern Azure Monitor alerts are **not** ingested here; query them via **Azure Resource Graph** (`alertsmanagementresources`). Do not build a primary alerting pipeline on this table; treat it as best-effort corroboration.
- **No `AlertType` and no `MonitorCondition` column.** The modern Azure Monitor **common alert schema** fields `alertType`, `monitorCondition` (Fired/Resolved), `monitorService`, `essentials.*` do **not** exist in this Log-Analytics table. Here, type is `AlertTypeNumber` / `AlertTypeDescription`, and "fired vs resolved" is expressed through `AlertState` + `TimeResolved` (resolved = `AlertState == "Closed"` / non-empty `TimeResolved`), **not** a `MonitorCondition` field. Queries written against the common-alert-schema names will not bind. *(Flagged to the orchestrator — the brief's column list mixed the modern schema with this legacy table.)*
- **`AlertSeverity` is a STRING, not an int.** Azure-sourced rows use `Sev0`–`Sev4`; SCOM-sourced rows use words (`Error`, `Warning`, `Information`). Filter as a string and account for both vocabularies; there is also a numeric `PriorityNumber` / `AlertStatus` that is *not* the severity.
- **`AlertContext` is XML, not JSON.** The forensic payload (which data item tripped the rule) is an **XML** string — there are **no `dynamic` columns** in this table. Use `parse_xml()` / `extract()`; `parse_json()` will not help.
- **Half the schema is SCOM carry-over.** `Custom1`–`Custom10`, `ManagementGroupName`, `RootObjectName`, `TicketId`, `ServiceDesk*`, `Remediation*`, `Flags*` come from Operations Manager and are usually blank for Azure Monitor alerts. `SourceSystem` tells you which producer a row came from (`Azure` vs `OpsManager` vs `Linux`).

## 🧪 Sample data
[`Alert_sample.csv`](Alert_sample.csv) — 19 rows. Tells the **Operation Quiet Ledger** story from the **infrastructure-alert** angle: as the compromise progresses on 2026-06-10, Azure Monitor alert rules fire on the affected resources — an **Activity-Log alert on `roleAssignments/write`** against `rg-finance-prod` (~09:42), a **Key Vault access-policy-change** Activity-Log alert and **Key Vault access-spike** metric alert on `kv-contoso-prod` (~09:55 / 10:15), a **storage-key-list** Activity-Log alert plus **egress / blob-transaction spike** metric alerts on `stcontosofin` (~10:02–10:09, the exfil), an **NSG security-rule-change** alert (~10:18), a **log-search alert on anomalous outbound data from `FIN-WS-07`** (~10:21), and a **failed-sign-in-burst** log alert for `alexw@contoso.com`. The Linux foothold surfaces as **SSH-auth-failure** and **sudo-to-root** alerts on `WEB-APP-01` (~08:52 / 09:24, `SourceSystem == "Linux"`). These sit amid **benign noise**: a CPU alert on FIN-WS-07, a storage-availability blip, a disk-space alert on HR-WS-03, a DC01 heartbeat miss, a cert-expiry reminder, an autoscale event, and a backup-completed notice — the normal daily churn an analyst must filter out. This corresponds to the **~09:40–11:00 privilege-escalation → Azure-pivot → exfil** window of the scenario.

The sample uses this curated subset of **real** columns: `TimeGenerated`, `TimeRaised`, `AlertName`, `AlertDescription`, `AlertSeverity`, `AlertPriority`, `AlertState`, `SourceSystem`, `SourceDisplayName`, `ResourceId`, `Query`, `ThresholdOperator`, `ThresholdValue`, `AlertValue`, `RepeatCount`.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · Control-plane alerts on a finance resource cluster during the incident window — [T1098.003](https://attack.mitre.org/techniques/T1098/003/)
**Hypothesis:** High-severity Activity-Log alerts (role write, Key Vault change, key list, NSG change) fire on `rg-finance-prod` resources within a tight window — the signature of a hands-on-keyboard Azure privilege-escalation + resource-abuse chain.
```kusto
Alert
| where TimeRaised between (datetime(2026-06-10T09:30:00Z) .. datetime(2026-06-10T11:00:00Z))
| where AlertSeverity in ("Sev0", "Sev1")
| where ResourceId has "rg-finance-prod"
| project TimeRaised, AlertName, AlertSeverity, AlertState, SourceDisplayName, ResourceId
| order by TimeRaised asc
```
**Triage:** True positive = role-write, Key-Vault-change, key-list and NSG-change alerts clustered within ~40 min on the same RG. Benign = a single expected change during an approved maintenance window, correlated to a ticket.

### H2 · Data-exfiltration corroboration — egress / transaction spikes on the finance storage account — [T1567.002](https://attack.mitre.org/techniques/T1567/002/)
**Hypothesis:** Metric alerts for egress and blob transactions on `stcontosofin` breach their thresholds by a wide margin, corroborating large outbound data movement.
```kusto
Alert
| where SourceDisplayName == "stcontosofin"
| where AlertName has_any ("Egress", "Transactions")
| where ThresholdOperator == "GreaterThan" and AlertValue > ThresholdValue
| extend BreachFactor = round(todouble(AlertValue) / todouble(ThresholdValue), 1)
| project TimeRaised, AlertName, AlertValue, ThresholdValue, BreachFactor, RepeatCount, AlertState
| order by TimeRaised asc
```
**Triage:** True positive = egress/transaction alerts firing for the first time today with `RepeatCount > 0` (sustained), minutes after a `listKeys` alert. Benign = a scheduled large copy/backup the storage team expects.

### H3 · Linux foothold — auth-failure and privilege-escalation alerts on a server — [T1110.001](https://attack.mitre.org/techniques/T1110/001/)
**Hypothesis:** A Linux host shows an SSH brute-force (failed-auth spike) alert followed by a sudo/privilege-escalation alert — a foothold being established and elevated.
```kusto
Alert
| where SourceSystem == "Linux"
| where AlertName has_any ("SSH", "sudo", "auth")
| project TimeRaised, AlertName, AlertSeverity, AlertState, SourceDisplayName, AlertValue, ThresholdValue
| order by TimeRaised asc
```
**Triage:** True positive = a brute-force spike on `WEB-APP-01` (~08:52) followed by sudo-to-root for a non-interactive account (~09:24). Benign = a noisy auth alert with no escalation follow-up, or a known automation account.

### H4 · Noise reduction — separate incident-window alerts from routine churn
**Hypothesis:** Most rows are benign operational churn; isolating high-severity, still-open alerts (`AlertState != "Closed"`) inside the incident window surfaces the few that matter.
```kusto
Alert
| where TimeRaised between (datetime(2026-06-10T08:30:00Z) .. datetime(2026-06-10T11:30:00Z))
| where AlertState in ("New", "Acknowledged")
| where AlertSeverity in ("Sev0", "Sev1", "Sev2")
| summarize Alerts = make_set(AlertName), n = count() by SourceDisplayName, SourceSystem
| order by n desc
```
**Triage:** True positive = `stcontosofin`, `kv-contoso-prod`, `rg-finance-prod`, `FIN-WS-07`, `WEB-APP-01` rising to the top with clustered Sev1/Sev2 alerts. Benign = single low-severity, already-`Closed` alerts (CPU, disk, autoscale, backup).

## 🔗 Correlates with
This table is the **infrastructure/health-alert** complement to the security-alert tables; the highest-value pivots are time-and-resource correlations into the underlying telemetry and into the security pipeline.

- **SecurityAlert** on `TimeRaised` ≈ alert time **and** `ResourceId` / host — the core pairing. `SecurityAlert` says "Defender/Sentinel flagged this as malicious"; `Alert` independently shows the *infra* fired at the same moment (egress spike, access spike, role-write alert). When both light up on the same resource in the same window, confidence in a true positive rises sharply, and `Alert` supplies threshold/observed-value evidence (`AlertValue` vs `ThresholdValue`) that `SecurityAlert` lacks. **They are different tables** — join them deliberately, never assume one contains the other.
- **SecurityIncident** on time-window + affected resource — during triage of a Sentinel incident, surface the `Alert` rows on the same resources/hosts in the incident's time range as supporting health/operational evidence (and to spot collateral impact the detections didn't model).
- **AzureActivity** on `ResourceId` / `_SubscriptionId` — the Activity-Log *alerts* here (role write, key list, NSG change, Key Vault write) are summaries; the **actor and outcome** behind each (`Caller`, `CallerIpAddress`, `OperationNameValue`, `ActivityStatusValue`) live in `AzureActivity`. Pivot to attribute the change.
- **Syslog** / **SecurityEvent** on `Computer` / `HostName` — for host log-search alerts (FIN-WS-07 outbound, WEB-APP-01 SSH/sudo), drop into the raw `Syslog` / `SecurityEvent` rows that the `Query` evaluated to see exactly what fired the rule.

## 📚 References
- Alert table reference (legacy) — https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/alert
- Query Azure Monitor alerts (the supported path — Azure Resource Graph) — https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/alerts-overview
- Common alert schema (modern `monitorCondition` / `alertType` fields, which this legacy table does NOT carry) — https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/alerts-common-schema
- SecurityAlert table reference (the distinct security-detection table) — https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/securityalert
