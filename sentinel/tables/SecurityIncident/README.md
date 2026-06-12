# SecurityIncident

> **Category:** Microsoft Sentinel (Solution: `SecurityInsights`)
> **Connector / source:** Microsoft Sentinel itself — written by the incident-management engine whenever an incident is **created or updated** (by an analytics rule grouping alerts, by an automation/playbook, or by an analyst action in the portal). Not an external data connector; it is Sentinel's own case-management audit stream.
> **Table plan:** Analytics (default). The reference flags **Basic log: No**, **Ingestion-time DCR support: Yes**, **Lake-only ingestion: Yes**.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/securityincident

## What this table is
Each row is **one snapshot of a Microsoft Sentinel incident at the moment it changed** — i.e. this is a **change log, not a current-state table**. An incident is the *case object* that bundles one or more `SecurityAlert` detections (plus bookmarks) into a single investigable unit with a human number, an owner, a severity, a status, and (on close) a classification. A **new row is written on every update**: creation, severity bump, owner assignment, status transition (New → Active → Closed), comment/label/task changes, and re-open. Because of this, the same incident appears many times with the same `IncidentNumber` / `IncidentName` but a rising `LastModifiedTime`. In a SOC this table is the backbone of **incident metrics and triage reporting** — mean-time-to-acknowledge / mean-time-to-resolve, open-incident queues, false-positive rates by classification, and analyst-workload dashboards — and it is the pivot from a case back down to its constituent alerts via `AlertIds`.

## ⚠️ Read this first — it is a change log, query with `arg_max`
Because every update emits a row, **never `SecurityIncident | where Status == "Active"`** directly (you will count stale historical states). To get the **current state of each incident**, collapse to the latest row per incident first:

```kusto
SecurityIncident
| summarize arg_max(LastModifiedTime, *) by IncidentNumber
```

Then filter the result. This single pattern underlies almost every correct SecurityIncident query — open-queue counts, severity breakdowns, MTTR. (`arg_max(TimeGenerated, *)` works too; `LastModifiedTime` is the semantically correct change clock.)

## Schema
Full column list, validated against the Microsoft Learn reference. Types are the KQL/Log Analytics types. Several columns are **dynamic** (JSON) — marked below — and must be parsed, not string-matched.

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | Timestamp (UTC) of when this incident snapshot was ingested (i.e. when the update happened). |
| IncidentNumber | int | The **sequential, human-facing** incident number (what analysts cite, e.g. `4471`). Stable across all updates of the same incident. |
| IncidentName | string | The **resource name / stable GUID** of the incident (the ARM resource name). Stable across updates; use as the durable join key. |
| Title | string | The incident title (rule/grouping-derived, editable by analysts). |
| Severity | string | Incident severity — `Informational`, `Low`, `Medium`, `High`. **String, not int.** Can change across updates. |
| Status | string | Lifecycle state — `New`, `Active`, `Closed`. The value you collapse with `arg_max` to get the current queue. |
| Classification | string | Disposition set **when closed**: `TruePositive`, `BenignPositive`, `FalsePositive`, `Undetermined`. Empty while open. |
| ClassificationReason | string | Reason code paired with the classification (e.g. `SuspiciousActivity`, `SuspiciousButExpected`, `InaccurateData`, `IncorrectAlertLogic`). Empty while open. |
| ClassificationComment | string | Free-text analyst note explaining the close reason. |
| Owner | dynamic | **JSON** describing the assignee — keys `objectId`, `email`, `assignedTo`, `userPrincipalName`. Empty/blank fields until someone is assigned. |
| AlertIds | dynamic | **JSON array** of the alert IDs grouped into this incident. These values join to **`SecurityAlert.SystemAlertId`**. Grows as more alerts are correlated in. |
| BookmarkIds | dynamic | JSON array of hunting-bookmark IDs attached to the incident. |
| Comments | dynamic | JSON array of comments added to the incident. |
| Labels | dynamic | JSON array of labels/tags applied to the incident. |
| Tasks | dynamic | JSON array of incident tasks (investigation checklist items). |
| RelatedAnalyticRuleIds | dynamic | JSON array of the analytics-rule IDs that produced the alerts in this incident. |
| AdditionalData | dynamic | JSON blob of extra incident metadata (alert/bookmark/comment counts, tactics, product names). |
| CreatedTime | datetime | Timestamp (UTC) the incident was first created. Constant across all updates. |
| FirstActivityTime | datetime | Timestamp (UTC) of the **earliest** underlying activity in the incident (from the alerts). |
| LastActivityTime | datetime | Timestamp (UTC) of the **latest** underlying activity in the incident. |
| FirstModifiedTime | datetime | Timestamp (UTC) of the first modification to the incident. |
| LastModifiedTime | datetime | Timestamp (UTC) of the **most recent** modification — the change clock you collapse on with `arg_max`. |
| ClosedTime | datetime | Timestamp (UTC) the incident was last closed. Empty while open. |
| ModifiedBy | string | The **source of this change** — an analyst UPN, `Microsoft Sentinel` (rule engine), or an automation/playbook identifier. Drives "who/what touched the case." |
| ProviderName | string | The source provider that generated the incident (e.g. `Azure Sentinel`). |
| ProviderIncidentId | string | The incident ID assigned by the provider (relevant when incidents originate outside Sentinel, e.g. Defender XDR sync). |
| IncidentUrl | string | Deep link to open the incident in the Sentinel/Defender portal. |
| Description | string | The incident description. |
| SourceSystem | string | Agent/source type that collected the record (e.g. `Azure`). |
| TenantId | string | The Log Analytics workspace ID. |
| Type | string | The name of the table (`SecurityIncident`). |
| _BilledSize | real | The record size in bytes. |
| _IsBillable | string | Whether ingesting the record is billable. |

> Every column from the Microsoft Learn reference is listed above (33 columns). Dynamic columns (`Owner`, `AlertIds`, `BookmarkIds`, `Comments`, `Labels`, `Tasks`, `RelatedAnalyticRuleIds`, `AdditionalData`) hold JSON and must be parsed with `parse_json` / `mv-expand` / dot-paths — never inventible.

## Key columns for detection & hunting
- **Identity:** there is no end-user/attacker identity on this table — the *subject* of an incident lives in its alerts (`SecurityAlert.Entities`), not here. The only identity columns are operational: the **owner** via `tostring(parse_json(Owner).userPrincipalName)` (or `.email`), and **who changed the case** via `ModifiedBy`.
- **Host / device:** n/a directly — hosts/devices are in the constituent alerts. Pivot through `AlertIds` → `SecurityAlert` to recover entities.
- **Network:** n/a — IPs live in the alerts/entities, not on the incident.
- **Outcome / result:** `Status` (`New`/`Active`/`Closed`) for lifecycle; `Classification` + `ClassificationReason` for the *disposition* once closed (true vs benign vs false positive). All are strings.
- **Timestamps:** `TimeGenerated` / `LastModifiedTime` (the update clock — use for `arg_max`); `CreatedTime` (case open); `FirstActivityTime` / `LastActivityTime` (underlying activity span); `ClosedTime` (case close). MTTA/MTTR are computed by differencing these.
- **Join keys (to other tables):** **`AlertIds` (dynamic array) → `SecurityAlert.SystemAlertId`** is the primary pivot from a case to its detections. `RelatedAnalyticRuleIds` → the analytics rules. `IncidentNumber` (human) and `IncidentName` (stable GUID) join updates of the same incident together. Within the table, collapse on `IncidentNumber` with `arg_max(LastModifiedTime, *)`.

## ⚠️ Schema gotchas
- **It is a change log — one row per UPDATE.** The single most important trap: a naive `count` or `where Status==...` over the raw table double-counts historical states. **Always `summarize arg_max(LastModifiedTime, *) by IncidentNumber` first.**
- **`IncidentNumber` (int) ≠ `IncidentName` (string GUID).** `IncidentNumber` is the human number analysts quote; `IncidentName` is the ARM resource name / stable GUID. Don't confuse them — and note `IncidentName` is *not* the human-readable title (that's `Title`).
- **`Severity` and `Status` are STRINGS**, not ints/enums (`"High"`, `"Active"`). Don't `toint()`; compare as strings, mind casing.
- **`Owner` and `AlertIds` are dynamic JSON**, not plain strings. `Owner` is an object (`parse_json(Owner).userPrincipalName`); `AlertIds` is an array (`mv-expand` or `parse_json(AlertIds)[0]`) — `==`-matching the raw string will not work.
- **`Classification` / `ClassificationReason` / `ClosedTime` are empty until the incident is closed.** Filter `isnotempty(ClosedTime)` before reasoning about disposition.
- **Owner fields are blank on `New` rows** — an unassigned incident has empty `objectId`/`email`/`userPrincipalName` inside the `Owner` JSON. "Acknowledged" is best modelled as the first transition to `Active` (or first non-empty owner), not the existence of the column.
- **`AlertIds` grows over the incident's life** as correlation pulls in more alerts — the *current* alert set is the array on the `arg_max` (latest) row, not the union of every historical row.

## 🧪 Sample data
[`SecurityIncident_sample.csv`](SecurityIncident_sample.csv) — 14 rows. The rows are the **incident change log for *Operation Quiet Ledger***: incident **#4471 "Suspected account compromise & data exfiltration – alexw"** walks New → Active (owner `dvora@contoso.com` assigned) → severity rising Medium → High → Closed `TruePositive` across six update rows, bundling more `SecurityAlert` IDs into `AlertIds` at each step; alongside a parallel **#4480** AKS-secret-access incident that is still **open at High** (the live queue), a benign **#4468** anonymous-IP sign-in **auto-closed `BenignPositive`** by an automation rule, and a **#4475** failed-logon incident closed `FalsePositive` — the noise that makes the metrics realistic.
The sample uses this curated subset of **real** columns: `TimeGenerated`, `IncidentNumber`, `IncidentName`, `Title`, `Severity`, `Status`, `Classification`, `ClassificationReason`, `Owner`, `AlertIds`, `CreatedTime`, `FirstActivityTime`, `LastActivityTime`, `ClosedTime`, `LastModifiedTime`, `ModifiedBy`. This is the **case-management / triage layer** of the cross-table attack scenario — `AlertIds` pivots down into `SecurityAlert.SystemAlertId`, and from there into the per-host evidence in `SecurityEvent`, `SigninLogs`, `StorageBlobLogs`, and `AKSAudit`.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · Current-state open High-severity incidents — [T1078](https://attack.mitre.org/techniques/T1078/)
**Hypothesis:** Any incident whose **latest** state is `New`/`Active` at `High` severity is an un-resolved, high-priority case that should be on the analyst queue right now.
```kusto
SecurityIncident
| summarize arg_max(LastModifiedTime, *) by IncidentNumber
| where Status in ("New", "Active") and Severity == "High"
| extend OwnerUpn = tostring(parse_json(Owner).userPrincipalName)
| project IncidentNumber, Title, Severity, Status, OwnerUpn,
          OpenAlerts = array_length(parse_json(AlertIds)),
          CreatedTime, LastModifiedTime
| sort by LastModifiedTime desc
```
**Triage:** True positive (worth attention) = an open High incident still unassigned or stale past SLA — here #4480 (AKS secret access). Benign = a High that is actually `Closed` on its latest row (correctly excluded by the `arg_max`).

### H2 · Mean-time-to-acknowledge (MTTA) per incident — [T1078](https://attack.mitre.org/techniques/T1078/)
**Hypothesis:** The gap between `CreatedTime` and the **first** transition to `Active` measures how long an incident sat un-triaged; long MTTA on real incidents is an operational risk.
```kusto
SecurityIncident
| extend OwnerUpn = tostring(parse_json(Owner).userPrincipalName)
| summarize CreatedTime = min(CreatedTime),
            FirstAcknowledged = minif(LastModifiedTime, Status == "Active"),
            FinalStatus = arg_max(LastModifiedTime, Status)
          by IncidentNumber, Title
| where isnotempty(FirstAcknowledged)
| extend MTTA_minutes = datetime_diff('minute', FirstAcknowledged, CreatedTime)
| project IncidentNumber, Title, CreatedTime, FirstAcknowledged, MTTA_minutes
| sort by MTTA_minutes desc
```
**Triage:** True signal = real incidents (#4471 ≈ 24 min, #4480 ≈ 17 min) acknowledged by a human. Auto-closed false positives (#4468, #4475) never reach `Active`, so they correctly drop out — they were dispositioned without acknowledgement.

### H3 · Incident → alert fan-out (recover the constituent detections) — [T1078](https://attack.mitre.org/techniques/T1078/)
**Hypothesis:** Expanding the latest `AlertIds` of a case lists exactly which `SecurityAlert.SystemAlertId` detections it groups — the starting point for entity-level investigation.
```kusto
SecurityIncident
| summarize arg_max(LastModifiedTime, *) by IncidentNumber
| where IncidentNumber == 4471
| mv-expand AlertId = parse_json(AlertIds) to typeof(string)
| project IncidentNumber, Title, Severity, Status, AlertId
// pivot: | join kind=inner SecurityAlert on $left.AlertId == $right.SystemAlertId
```
**Triage:** True positive = a closed-`TruePositive` case (#4471) fanning out to 5 alerts spanning sign-in → process → exfil; each `AlertId` should resolve in `SecurityAlert`. Benign = a single-alert auto-closed case.

### H4 · Close-disposition quality — false-positive rate by reason — [T1078](https://attack.mitre.org/techniques/T1078/)
**Hypothesis:** Profiling `Classification` / `ClassificationReason` on closed incidents shows detection quality; a high `FalsePositive` rate flags rules that need tuning.
```kusto
SecurityIncident
| summarize arg_max(LastModifiedTime, *) by IncidentNumber
| where Status == "Closed"
| summarize Incidents = count() by Classification, ClassificationReason
| sort by Incidents desc
```
**Triage:** True signal = clusters of `FalsePositive` / `BenignPositive` (here the auto-closed VPN sign-in and the failed-logon case) pointing at noisy rules; `TruePositive` (#4471) confirms the real intrusion was dispositioned correctly.

## 🔗 Correlates with
- **SecurityAlert** on `AlertIds` (dynamic array) ↔ `SystemAlertId` — **the primary pivot.** `mv-expand` the latest `AlertIds`, then join to recover the alerts (and their `Entities`: users, IPs, hosts) that make up the case. This is how you go from "incident #4471" to "alexw / 185.220.101.2 / FIN-WS-07 / stcontosofin."
- **SecurityAlert** on `RelatedAnalyticRuleIds` ↔ the rule's `AlertType` / rule ID — identify which analytics rules drove the incident.
- **SecurityEvent / SigninLogs / StorageBlobLogs / AKSAudit** — *indirectly*, by first resolving `AlertIds` → `SecurityAlert.Entities`, then pivoting on the recovered `Account` / `IPAddress` / `Computer` / resource into the raw evidence tables.
- This table is the **top of the funnel** for triage: it is mostly standalone for *metrics* (MTTA/MTTR/queues via `arg_max`), but for *investigation* its one essential outward pivot is `AlertIds` → `SecurityAlert`.

## 📚 References
- SecurityIncident table reference — https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/securityincident
- Microsoft Sentinel incident investigation & management — https://learn.microsoft.com/en-us/azure/sentinel/investigate-cases
- Microsoft Sentinel incident metrics / `SecurityIncident` for reporting — https://learn.microsoft.com/en-us/azure/sentinel/manage-soc-with-incident-metrics
