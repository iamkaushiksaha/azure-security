# SecurityAlert

> **Category:** Security (Microsoft Sentinel / Microsoft Defender)
> **Connector / source:** Security **alerts** surfaced into Log Analytics by **Microsoft Sentinel** and connected security products — Microsoft Defender XDR (Defender for Endpoint / Identity / Office 365 / Cloud Apps), Microsoft Defender for Cloud, Microsoft Entra ID Protection, and **Sentinel analytics rules** (Scheduled / NRT / Fusion). Resource type `microsoft.securityinsights/securityinsights`.
> **Table plan:** Analytics (default). The reference flags **Basic log: No**, **Ingestion-time DCR support: Yes**, **Lake-only ingestion: Yes**.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/securityalert

> ⚠️ **This is `SecurityAlert` — NOT the Azure Monitor `Alert` table.**
> `SecurityAlert` = **security detections** ("a security product thinks this is malicious/suspicious"): MDE/MDC/MDO/Entra ID Protection alerts and Sentinel analytic-rule alerts. The Azure Monitor [`Alert`](../Alert/README.md) table = **infrastructure/health** alerts (a CPU metric crossing a threshold, a scheduled query returning rows). Different producers, different schemas. Build security detections, dashboards and joins on **this** table — the unique id is `SystemAlertId`, severity is `AlertSeverity`, and the affected account/host/IP live inside the `Entities` JSON, not in flat columns.

## What this table is
Each row is **one security alert** raised by a detection product and ingested into the workspace — a Defender for Endpoint behavioral alert, a Defender for Cloud cloud-resource alert, a Defender for Office 365 phish verdict, an Entra ID Protection risk detection, or an alert produced by a **Sentinel analytics rule** (Scheduled, NRT, or Fusion correlation). Rows appear within minutes of the detection firing and are **updated in place** as the alert's `Status` moves through New → InProgress → Resolved/Dismissed. The alert's substance is in three places: `AlertName`/`AlertType` (what fired), `AlertSeverity`/`Tactics`/`Techniques` (how bad + the ATT&CK mapping), and the `Entities` / `ExtendedProperties` JSON (who/what it touched and the evidence). In a SOC this is the **detection layer** that sits on top of the raw telemetry tables (SigninLogs, Device\*, SecurityEvent, StorageBlobLogs…): you triage alerts here, then pivot down into the telemetry for the full story — and alerts are **grouped into `SecurityIncident`** for case management.

## Schema
Full column list, validated against the Microsoft Learn reference. Types are the KQL/Log Analytics types. Note: several "detail blob" columns are typed **`string`** on the reference but carry **JSON** payloads — see gotchas.

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | When the alert record was ingested (use for time filtering). |
| StartTime | datetime | Start of the activity the alert covers (event time). |
| EndTime | datetime | End of the activity the alert covers (event time). |
| ProcessingEndTime | datetime | When the alert finished processing. |
| SystemAlertId | string | **Unique identifier of the alert instance.** The id used to join to `SecurityIncident.AlertIds`. |
| AlertName | string | Name of the alert / detection. |
| DisplayName | string | Display name of the alert (often equals `AlertName`; provider-formatted). |
| AlertType | string | Detection/type identifier of the alert (e.g. `WindowsDefenderAtp`, `RiskySignIn`, `Fusion`). |
| AlertSeverity | string | **Severity as a STRING:** `Informational`, `Low`, `Medium`, `High`. |
| Description | string | Human-readable description of what the alert detected. |
| ProviderName | string | The detection provider/engine (e.g. `MDATP`, `IPC`, `OATP`, `Microsoft Defender for Cloud`, `ASI Scheduled Alerts`, `Azure Sentinel`). |
| ProductName | string | Product that produced the alert (e.g. `Microsoft Defender Advanced Threat Protection`, `Azure Active Directory Identity Protection`, `Microsoft Defender for Office 365`, `Azure Security Center`, `Azure Sentinel`). |
| ProductComponentName | string | Sub-component of the product that emitted the alert. |
| VendorName | string | Vendor of the product (e.g. `Microsoft`). |
| VendorOriginalId | string | The vendor's own id for the alert (provider-side correlation id). |
| Status | string | Alert lifecycle state: `New`, `InProgress`, `Resolved`, `Dismissed`. |
| CompromisedEntity | string | Display name of the **main entity** the alert is about (a UPN, host name, or resource id/name). |
| Tactics | string | MITRE ATT&CK **tactic(s)** (comma/semicolon-separated names, e.g. `CredentialAccess`, `Exfiltration`). |
| Techniques | string | MITRE ATT&CK **technique id(s)** — a JSON-ish string (e.g. `["T1003.001"]`). |
| SubTechniques | string | MITRE ATT&CK sub-technique id(s), when provided. |
| Entities | string | **JSON array** of the entities involved (accounts, hosts, IPs, files, processes, URLs, mailboxes, azureResources). **The flat identities live HERE.** |
| ExtendedProperties | string | **JSON object** of provider-specific key/value evidence (process names, command lines, blob counts, client IPs, …). |
| ExtendedLinks | string | JSON of extra links/resources for the alert. |
| RemediationSteps | string | Recommended remediation steps (often a JSON array of strings). |
| ConfidenceLevel | string | Provider confidence level (e.g. `Low`/`High`), when supplied. |
| ConfidenceScore | real | Numeric confidence score, when supplied. |
| AlertLink | string | Deep link to the alert in the producing portal. |
| IsIncident | bool | Whether the alert is/was promoted to an incident. |
| SourceComputerId | string | Agent/source computer GUID (for host-sourced alerts). |
| ResourceId | string | Azure resource id associated with the alert. |
| WorkspaceResourceGroup | string | Resource group of the Log Analytics workspace. |
| WorkspaceSubscriptionId | string | Subscription id of the Log Analytics workspace. |
| Type | string | The name of the table (`SecurityAlert`). |
| _BilledSize | real | The record size in bytes (platform). |
| _IsBillable | string | Whether ingesting the data is billable (platform). |

> **~36 columns** total on the reference — every one is listed above. The detection-critical columns are `SystemAlertId`, `AlertName`/`DisplayName`/`AlertType`, `AlertSeverity`, `ProviderName`/`ProductName`, `Status`, `Tactics`/`Techniques`, `Entities`, `ExtendedProperties`, `CompromisedEntity`, `StartTime`/`EndTime`, `IsIncident`.

## Key columns for detection & hunting
- **Identity:** No flat UPN column — the account is inside `Entities`. Extract with `mv-expand` + filter `Type == "account"`, then `tostring(parse_json(Entities)[i].Name)` / `.UPNSuffix` / `.AadUserId`. `CompromisedEntity` often holds the primary UPN as a convenience string.
- **Host / device:** Also in `Entities` (`Type == "host"`: `.HostName`, `.AzureID` = the Defender/AAD device id, `.OSFamily`). `CompromisedEntity` holds the host name for endpoint alerts.
- **Network:** IPs are `Entities` of `Type == "ip"` (`.Address`, `.Location.CountryCode`). Also frequently mirrored in `ExtendedProperties` (e.g. `ClientIp`, `CallerIpAddress`, `AttackerIp`).
- **Outcome / result:** This table records **that a detection fired** — there is no success/failure column. Severity is `AlertSeverity` (**string**: `Informational`/`Low`/`Medium`/`High`); lifecycle is `Status` (`New`/`InProgress`/`Resolved`/`Dismissed`); `IsIncident` flags promotion.
- **Timestamps:** `TimeGenerated` (ingestion), `StartTime`/`EndTime` (the activity window the alert covers).
- **Join keys (to other tables):** `SystemAlertId` (→ `SecurityIncident.AlertIds`), entities extracted from `Entities` — account UPN/AadUserId (→ `SigninLogs`, `IdentityInfo`), host `AzureID`/HostName (→ `DeviceEvents`/`DeviceLogonEvents`, `SecurityEvent`), IP `Address` (→ any network/TI table), azureResource `ResourceId` (→ `AzureActivity`, `StorageBlobLogs`).

## ⚠️ Schema gotchas
- **The id is `SystemAlertId`, not `AlertId`.** There is no `AlertId` column. Joins to `SecurityIncident` are `SystemAlertId` ↔ a member of the `AlertIds` array (`where AlertIds has SystemAlertId` / `mv-expand AlertIds`).
- **Severity is `AlertSeverity` (string), not `Severity`.** Values are words (`Informational`/`Low`/`Medium`/`High`), **not** the `Sev0`–`Sev4` of the Azure Monitor `Alert` table and **not** an int. Filter as a string.
- **The flat identities are inside `Entities`.** There are no top-level `UserPrincipalName` / `DeviceName` / `IPAddress` columns — account, host and IP live in the `Entities` JSON array (each element has a `Type` discriminator: `account`, `host`, `ip`, `file`, `process`, `url`, `mailbox`/`mailMessage`, `azureResource`, `dnsResolution`…). You must `mv-expand`/`parse_json` to query them.
- **`Entities`, `ExtendedProperties`, `Techniques`, `ExtendedLinks`, `RemediationSteps` are typed `string` but hold JSON.** Wrap with `parse_json()` (or `todynamic()`) before indexing — `Entities` is a JSON **array**, `ExtendedProperties` a JSON **object**. Property **names inside these blobs vary by provider** (an MDE alert and a Defender-for-Cloud alert use different `ExtendedProperties` keys), so code defensively.
- **Provider vocab is inconsistent.** `ProviderName` mixes short codes (`MDATP`, `IPC`, `OATP`) with full strings (`Microsoft Defender for Cloud`, `Azure Sentinel`, `ASI Scheduled Alerts`); `ProductName` likewise (`Azure Security Center` is Defender for Cloud's legacy product name). Match with `has`/`in`, not exact equality, when you want "all alerts from product X".

## 🧪 Sample data
[`SecurityAlert_sample.csv`](SecurityAlert_sample.csv) — 18 rows. This is the **detection layer of Operation Quiet Ledger**: the alerts that fired across the whole intrusion on 2026-06-10 — MDO **"Phishing email detected"** (delivered to alexw) → Entra ID Protection **"Atypical travel / risky sign-in"** for `alexw` from `185.220.101.2` (NL) → MDE **"Suspicious remote logon"**, **"Suspicious PowerShell command line"** and **"LSASS access"** on `FIN-WS-07` → MDC **"SSH brute force succeeded"** on `WEB-APP-01` → MDE C2/DGA and **DC01** spray-then-logon → MDC **"Anomalous granting of permissions"** (Owner role) and **"Access from a suspicious IP to a storage account"** (`listKeys` on `stcontosofin`) → a **Sentinel custom scheduled rule "Mass blob download"** → MDC Key Vault secret access and an AKS **cluster-admin** binding → a **Sentinel Fusion** "Data exfiltration" correlation tying `listKeys`+mass-GetBlob to `alexw`/the Tor IP. Two **benign/low** alerts (an EICAR `Antimalware Action Taken` on `HR-WS-03`, a `Low` "atypical sign-in" for `jamest` from London, and a blocked invoice-phish) provide the signal-vs-noise. Each row's `Tactics`/`Techniques` is mapped to the real ATT&CK of that kill-chain step, and the `Entities` JSON carries `alexw`/`FIN-WS-07`/`185.220.101.2` so it joins to the other tables.

The sample uses this curated subset of **real** columns: `TimeGenerated`, `StartTime`, `EndTime`, `SystemAlertId`, `AlertName`, `DisplayName`, `AlertType`, `AlertSeverity`, `ProviderName`, `ProductName`, `VendorName`, `Status`, `CompromisedEntity`, `Tactics`, `Techniques`, `Entities`, `ExtendedProperties`, `IsIncident`.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · High-severity alerts in a tight window mapped to ATT&CK — [T1059.001](https://attack.mitre.org/techniques/T1059/001/)
**Hypothesis:** A burst of `High`/`Medium` alerts across multiple providers within one window — the signature of a live hands-on-keyboard intrusion rather than isolated noise.
```kusto
SecurityAlert
| where TimeGenerated between (datetime(2026-06-10T08:00:00Z) .. datetime(2026-06-10T11:30:00Z))
| where AlertSeverity in ("High", "Medium")
| project TimeGenerated, AlertName, AlertSeverity, ProviderName, CompromisedEntity, Tactics, Techniques
| order by TimeGenerated asc
```
**Triage:** True positive = MDE/MDC/IPC/Sentinel all firing on the same cast (`alexw`, `FIN-WS-07`, `stcontosofin`) within hours, walking the kill chain. Benign = one-off `Low`/`Informational` alerts already `Resolved`/`Dismissed`.

### H2 · Extract entities from the `Entities` JSON — find every alert touching the attacker IP — [T1078.004](https://attack.mitre.org/techniques/T1078/004/)
**Hypothesis:** The compromise IP `185.220.101.2` appears as an entity across alerts from *different* products — pivoting on the IP inside `Entities` stitches the campaign together.
```kusto
SecurityAlert
| extend Ents = parse_json(Entities)
| mv-expand Ent = Ents
| where tostring(Ent.Type) == "ip"
| extend AlertIp = tostring(Ent.Address), Country = tostring(Ent.Location.CountryCode)
| where AlertIp == "185.220.101.2"
| project TimeGenerated, AlertName, AlertSeverity, ProviderName, AlertIp, Country, CompromisedEntity
| order by TimeGenerated asc
```
**Triage:** True positive = the same NL Tor IP driving risky sign-in, RDP, DC spray, RBAC write, storage access and exfil. Benign = a corporate egress IP (e.g. `20.98.111.30`, GB) showing up on a single low-risk alert.

### H3 · Group alerts by `CompromisedEntity` — which asset is the blast-radius hub — [T1110](https://attack.mitre.org/techniques/T1110/)
**Hypothesis:** Ranking entities by how many distinct alerts and tactics name them surfaces the patient-zero host/account driving the incident.
```kusto
SecurityAlert
| where AlertSeverity != "Informational"
| summarize
    Alerts   = count(),
    Highs    = countif(AlertSeverity == "High"),
    Tactics  = make_set(Tactics),
    Providers= make_set(ProviderName),
    FirstSeen= min(StartTime),
    LastSeen = max(EndTime)
    by CompromisedEntity
| order by Alerts desc
```
**Triage:** True positive = `FIN-WS-07` (and `alexw@contoso.com`, `stcontosofin`) rising to the top with many alerts spanning Execution→CredentialAccess→Exfiltration. Benign = `HR-WS-03`/`jamest@contoso.com` with a single low/informational alert.

### H4 · Open, incident-promoted alerts that still need triage — [T1530](https://attack.mitre.org/techniques/T1530/)
**Hypothesis:** Alerts with `IsIncident == true` that are still `New`/`InProgress` are the live workload an analyst must action first.
```kusto
SecurityAlert
| where IsIncident == true
| where Status in ("New", "InProgress")
| project TimeGenerated, AlertName, AlertSeverity, ProviderName, Status, CompromisedEntity, Tactics
| order by AlertSeverity asc, TimeGenerated asc
```
**Triage:** True positive = the High-severity exfil/cred-access alerts (`Mass blob download`, `LSASS access`, `listKeys`) open and unworked. Benign = already-`Resolved`/`Dismissed` alerts (EICAR test, blocked phish) that correctly carry `IsIncident == false`.

## 🔗 Correlates with
- **SecurityIncident** on `SystemAlertId` ↔ `AlertIds` — the **primary pivot**. Sentinel groups these alerts into incidents; `SecurityIncident.AlertIds` is an array of `SystemAlertId` values. Join `where AlertIds has SystemAlertId` (or `mv-expand AlertIds`) to see which case an alert belongs to, and to enumerate every alert in an incident.
- **SigninLogs** on the account UPN / `AadUserId` extracted from `Entities` (and the IP) — the Entra ID Protection "risky sign-in" alert here is the *detection*; `SigninLogs` holds the raw sign-ins (failures→success, risk level) that triggered it, e.g. the 08:20 `alexw` success from `185.220.101.2`.
- **DeviceLogonEvents / DeviceEvents / SecurityEvent** on the host (`AzureID`/HostName from `Entities`, or `CompromisedEntity`) — drop from an MDE alert (`Suspicious remote logon`, `LSASS access`, `Suspicious PowerShell`) into the raw endpoint telemetry on `FIN-WS-07`/`DC01` that the detection fired on.
- **AzureActivity / StorageBlobLogs** on the azureResource `ResourceId` (and IP) — the MDC/Sentinel storage and RBAC alerts (`listKeys`, `Mass blob download`, role write) are summaries; the control-plane and data-plane truth is in `AzureActivity` (`OperationNameValue`, `Caller`, `CallerIpAddress`) and `StorageBlobLogs` (the GetBlob exfil burst on `stcontosofin`).

## 📚 References
- SecurityAlert table reference — https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/securityalert
- Microsoft Sentinel **entities reference** (the `Entities` JSON schema: account/host/ip/file/process/azureResource…) — https://learn.microsoft.com/en-us/azure/sentinel/entities-reference
- SecurityIncident table reference (the case the alerts roll up into) — https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/securityincident
- Microsoft Sentinel — schedule-based and Fusion analytics rules (producers of Sentinel-sourced rows) — https://learn.microsoft.com/en-us/azure/sentinel/detect-threats-built-in
