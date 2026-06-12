# AuditLogs

> **Category:** Microsoft Entra ID (Azure Resources, Security)
> **Connector / source:** Microsoft Entra ID diagnostic settings → "AuditLogs" log category (directory activity), streamed to Log Analytics / Microsoft Sentinel. This is the Log Analytics projection of the Microsoft Graph `directoryAudit` resource (`microsoft.graph/tenants`).
> **Table plan:** Analytics (default). The reference flags **Basic log: No**; ingestion-time DCR transforms and lake-only ingestion are supported.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/auditlogs

## What this table is
Each row is a single **administrative / directory change** in Microsoft Entra ID (Azure AD) — a write to the directory such as creating a user, adding a member to a group or a directory role, registering or consenting to an application, resetting a password, or changing a policy. Rows appear continuously, within minutes, for every audited directory operation regardless of who performed it (an admin, a user self-servicing, or a service principal). In a SOC this is the primary table for **post-compromise directory abuse and persistence**: privileged role assignments ("Add member to role"), OAuth consent grants to attacker apps, app-role assignments and credential (secret/certificate) additions to service principals, group membership changes, and password resets. It pairs with `SigninLogs` — the sign-in tells you an identity authenticated; AuditLogs tells you what that identity then *changed*.

**Underlying Graph model:** the nested objects from the Graph `directoryAudit` resource become this table's dynamic columns. Graph `initiatedBy` (a `userIdentity` / `appIdentity` union) → **`InitiatedBy`** (so the actor's UPN/IP/app name is nested, *not* a flat column); Graph `targetResources[]` → the **`TargetResources`** array (the objects that were changed, plus per-property `modifiedProperties` old/new values); Graph `additionalDetails[]` → **`AdditionalDetails`**. Graph `activityDisplayName` → `ActivityDisplayName`, `loggedByService` → `LoggedByService`, `result` → `Result`.

## Schema
Full column list, validated against the Microsoft Learn reference. Types are the KQL/Log Analytics types. Dynamic (nested JSON) columns are marked **dyn**.

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | When the record was created/ingested (use for time filtering). |
| ActivityDateTime | datetime | When the activity was performed (event time), UTC. |
| AADOperationType | string | Type of operation: `Add`, `Update`, `Delete`, `Other`. |
| AADTenantId | string | ID of the Entra (AAD) tenant. |
| ActivityDisplayName | string | Activity / operation name, e.g. `Add member to role`, `Create user`, `Consent to application`. (See the Entra audit activity list.) |
| AdditionalDetails | **dyn** | Additional details on the activity (key/value pairs). |
| Category | string | Audit category of the operation — e.g. `RoleManagement`, `UserManagement`, `GroupManagement`, `ApplicationManagement`. |
| CorrelationId | string | Optional GUID passed by the client; correlates client- and server-side operations across services. **Key cross-table join.** |
| DurationMs | long | Not used — can be ignored. |
| Id | string | GUID that uniquely identifies the activity (the audit record ID). |
| Identity | string | Identity from the token presented when the request was made (user, system, or service principal) — a display string, not the structured actor. |
| InitiatedBy | **dyn** | **The actor.** `user` (`userPrincipalName`, `id`, `displayName`, `ipAddress`) for user-driven actions, or `app` (`displayName`, `appId`, `servicePrincipalId`) for app-driven actions. |
| Level | string | Message type — currently always `Informational`. |
| Location | string | Datacenter location. |
| LoggedByService | string | Service that initiated/logged the activity, e.g. `Core Directory`, `PIM`, `Self-service Password Management`, `B2C`, `Invited Users`, `MIM Service`. |
| OperationName | string | Name of the operation (often mirrors `ActivityDisplayName`). |
| OperationVersion | string | REST API version requested by the client. |
| Result | string | Result of the activity: `success`, `failure`, `timeout`, `unknownFutureValue`. |
| ResultDescription | string | Additional description of the result. |
| ResultReason | string | Cause of a failure or timeout result. |
| ResultType | string | Result of the operation: `Success` / `Failure` (a coarser twin of `Result`). |
| ResultSignature | string | Not used — can be ignored. |
| TargetResources | **dyn** | **Array** of the objects changed by the activity. Each element: `id`, `displayName`, `type` (`User`/`Device`/`Directory`/`App`/`Role`/`Group`/`Policy`/`ServicePrincipal`/`Other`), `userPrincipalName`, and `modifiedProperties[]` (`displayName`, `oldValue`, `newValue`). |
| Resource | string | (generic resource string; usually empty for this table). |
| ResourceGroup | string | (generic; usually empty). |
| ResourceId | string | (generic; usually empty). |
| ResourceProvider | string | (generic; usually empty). |
| SourceSystem | string | Collecting agent type — `Azure` for this table. |
| Type | string | Table name (`AuditLogs`). |

> **~31 columns** total. Above lists every column from the reference. The detection-relevant ones are the two dynamic blobs `InitiatedBy` / `TargetResources` (plus `AdditionalDetails`), the `Category` / `ActivityDisplayName` / `OperationName` triplet, and `Result` / `ResultReason` / `CorrelationId` / `Id`. Trailing generic/platform columns carry standard values: `_BilledSize` (real), `_IsBillable` (string), `OperationVersion`, `ResultSignature`, `DurationMs`, `Resource`, `ResourceGroup`, `ResourceId`, `ResourceProvider`.

## Key columns for detection & hunting
- **Identity (actor):** **nested** — `tostring(InitiatedBy.user.userPrincipalName)`, `tostring(InitiatedBy.user.id)` (the object GUID, = SigninLogs `UserId`), `tostring(InitiatedBy.user.ipAddress)`. For app/service-principal actors use `tostring(InitiatedBy.app.displayName)` / `tostring(InitiatedBy.app.servicePrincipalId)`. **There is no flat `UserPrincipalName` or `IPAddress` column.**
- **Target:** **nested array** `TargetResources` — `tostring(TargetResources[0].displayName)`, `tostring(TargetResources[0].type)`, `tostring(TargetResources[0].userPrincipalName)`; `mv-expand TargetResources` when there can be more than one, and drill into `TargetResources[0].modifiedProperties` for the old/new values of what changed (e.g. the role display name).
- **Host / device:** n/a (directory operations have no endpoint host; a target *can* be a `Device` object).
- **Network:** the actor source IP is nested: `tostring(InitiatedBy.user.ipAddress)`. No dedicated network columns.
- **Outcome / result:** `Result` (`success` / `failure` / `timeout` / `unknownFutureValue`); reason in `ResultReason`. `ResultType` is a coarser `Success`/`Failure` twin.
- **Timestamps:** `TimeGenerated` (ingest) and `ActivityDateTime` (when the change happened).
- **Join keys (to other tables):** `CorrelationId` (→ `SigninLogs` for the sign-in that preceded the change; → `AzureActivity` for the ARM action it triggered), `tostring(InitiatedBy.user.id)` ↔ SigninLogs `UserId`, `tostring(InitiatedBy.user.userPrincipalName)` ↔ SigninLogs `UserPrincipalName` / AzureActivity `Caller`, `AADTenantId`.

## ⚠️ Schema gotchas
- **The actor is NOT a flat column.** Many authors reach for `UserPrincipalName` / `IPAddress` — they don't exist here. The actor lives in the dynamic `InitiatedBy`: `tostring(InitiatedBy.user.userPrincipalName)` (and `InitiatedBy.user.ipAddress`). App-initiated rows populate `InitiatedBy.app` instead, with `InitiatedBy.user` null — handle both branches or you'll drop service-principal activity (often the interesting persistence).
- **`TargetResources` is a dynamic ARRAY, not an object.** Index it (`TargetResources[0]`) or `mv-expand` it; never `tostring()` the whole array and string-match. The *meaningful* detail (which role, which credential, old→new value) is one level deeper in `TargetResources[0].modifiedProperties[]`.
- **Two result columns, two vocabularies.** `Result` uses `success`/`failure`/`timeout`/`unknownFutureValue` (lowercase); `ResultType` uses `Success`/`Failure`. Filter on `Result` and match its exact lowercase values.
- **`Category` is the audit area, not "Audit".** Despite the reference's terse note, real data populates `Category` with the operation area (`RoleManagement`, `ApplicationManagement`, `UserManagement`, `GroupManagement`, `DirectoryManagement`, …) — pivot on it to scope a hunt.
- **`DurationMs`, `ResultSignature` are not used; `Level` is always `Informational`.** Don't build logic on them.
- **Interactive *and* programmatic both land here.** A role added in the portal and the same change via Microsoft Graph PowerShell are both audited; correlate with `SigninLogs` on `CorrelationId` to recover *how* (which app/IP) the actor was authenticated.

## 🧪 Sample data
[`AuditLogs_sample.csv`](AuditLogs_sample.csv) — 22 rows. Tells the **Operation Quiet Ledger** Entra privilege-escalation step (~09:38–09:46): the compromised `alexw@contoso.com` — authenticated via Microsoft Graph PowerShell from attacker IP `185.220.101.2` — adds himself to the **Privileged Role Administrator** directory role, adds the abused `svc-backup@contoso.com` automation account to **Application Administrator**, grants an **app-role assignment** and an OAuth **delegated consent** to a suspicious app (`Contoso Finance Sync`), and adds an app credential (client secret) for persistence — all `Result = success`. This sits against a backdrop of legitimate directory administration by `itadmin@contoso.com` and `dvora@contoso.com` (group/user management, an SSPR reset) and one benign app-initiated provisioning row. This is the **09:40 privilege-escalation** step of the cross-table scenario, downstream of the 08:20 risky sign-in and upstream of the 10:00 Azure role write.

The sample uses this curated subset of **real** columns: `TimeGenerated`, `ActivityDateTime`, `OperationName`, `ActivityDisplayName`, `Category`, `AADOperationType`, `Result`, `ResultReason`, `LoggedByService`, `InitiatedBy`, `TargetResources`, `AdditionalDetails`, `CorrelationId`, `Id`, `AADTenantId`. The dynamic columns hold valid JSON (`InitiatedBy` = actor object with `user`/`app`; `TargetResources` = array with `modifiedProperties`).

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · Member added to a privileged directory role — [T1098.003](https://attack.mitre.org/techniques/T1098/003/)
**Hypothesis:** A principal was added to a high-privilege Entra directory role (Global / Privileged Role / Application / User Administrator) — classic post-compromise privilege escalation and persistence.
```kusto
AuditLogs
| where ActivityDisplayName == "Add member to role"
| where Result == "success"
| extend RoleName = tostring(TargetResources[0].modifiedProperties[0].newValue)
| extend Role = iif(isempty(RoleName), tostring(TargetResources[0].displayName), RoleName)
| extend ActorUPN = tostring(InitiatedBy.user.userPrincipalName),
         ActorIP  = tostring(InitiatedBy.user.ipAddress),
         TargetUPN = tostring(TargetResources[0].userPrincipalName)
| where Role has_any ("Global Administrator", "Privileged Role Administrator",
                      "Application Administrator", "User Administrator",
                      "Privileged Authentication Administrator")
| project TimeGenerated, ActorUPN, ActorIP, Action = ActivityDisplayName, Role, TargetUPN, CorrelationId
| order by TimeGenerated asc
```
**Triage:** True positive = role added by a non-admin actor and/or from a non-corporate IP (here `alexw` from `185.220.101.2`), or self-assignment. Benign = a known identity-admin (`itadmin`) granting a role from a corporate IP as part of a change ticket.

### H2 · OAuth consent / app-role granted to an application — [T1528](https://attack.mitre.org/techniques/T1528/)
**Hypothesis:** A delegated OAuth consent or an app-role assignment was granted to a service principal — illicit consent / app-based persistence that survives password resets and MFA.
```kusto
AuditLogs
| where Category == "ApplicationManagement"
| where ActivityDisplayName in ("Consent to application",
                                "Add app role assignment grant to user",
                                "Add app role assignment to service principal",
                                "Add delegated permission grant",
                                "Add service principal credentials")
| where Result == "success"
| extend ActorUPN = tostring(InitiatedBy.user.userPrincipalName),
         ActorApp = tostring(InitiatedBy.app.displayName),
         ActorIP  = tostring(InitiatedBy.user.ipAddress),
         TargetApp = tostring(TargetResources[0].displayName)
| project TimeGenerated, Activity = ActivityDisplayName,
          Actor = coalesce(ActorUPN, ActorApp), ActorIP, TargetApp, CorrelationId
| order by TimeGenerated asc
```
**Triage:** True positive = consent/app-role/secret-add for an unfamiliar app (here `Contoso Finance Sync`) from a risky actor/IP, especially `Add service principal credentials` (a new secret on an existing SP). Benign = first-party Microsoft apps or an admin onboarding a vetted SaaS app.

### H3 · Directory changes by an actor from an attacker IP — [T1098](https://attack.mitre.org/techniques/T1098/)
**Hypothesis:** Any audited directory change whose actor source IP is a known-bad / non-corporate address — scopes *everything* the compromised identity touched in the directory, not just roles.
```kusto
let badIPs = dynamic(["185.220.101.2", "91.219.236.18"]);
AuditLogs
| extend ActorUPN = tostring(InitiatedBy.user.userPrincipalName),
         ActorIP  = tostring(InitiatedBy.user.ipAddress)
| where ActorIP in (badIPs)
| summarize Operations = make_set(ActivityDisplayName),
            Targets = make_set(tostring(TargetResources[0].displayName)),
            Count = count(),
            FirstSeen = min(TimeGenerated), LastSeen = max(TimeGenerated)
        by ActorUPN, ActorIP
| order by Count desc
```
**Triage:** True positive = a finance/standard user (here `alexw`) performing role/app management from a foreign hosting IP within minutes. Benign = none for hard-coded attacker IPs; generalise by replacing `badIPs` with "IP not in the corporate egress set".

### H4 · Self-service-style password reset on another user — [T1098](https://attack.mitre.org/techniques/T1098/)
**Hypothesis:** A password was reset/changed where the actor is not a recognised identity admin, or actor ≠ target — possible account-takeover persistence.
```kusto
AuditLogs
| where Category in ("UserManagement") and ActivityDisplayName has "password"
| where Result == "success"
| extend ActorUPN = tostring(InitiatedBy.user.userPrincipalName),
         TargetUPN = tostring(TargetResources[0].userPrincipalName)
| extend SelfService = (ActorUPN == TargetUPN)
| project TimeGenerated, ActivityDisplayName, ActorUPN, TargetUPN, SelfService,
          LoggedByService, CorrelationId
| order by TimeGenerated asc
```
**Triage:** True positive = reset of a privileged or unrelated account by a non-admin actor. Benign = `Self-service Password Management` where actor == target, or `itadmin` performing a help-desk reset.

## 🔗 Correlates with
- **SigninLogs** on `CorrelationId` (and `InitiatedBy.user.id` ↔ `UserId`, `InitiatedBy.user.userPrincipalName` ↔ `UserPrincipalName`) — recover *how* the actor authenticated (app, IP, risk level) for each directory change; ties the 09:40 role adds back to `alexw`'s 08:20 risky sign-in and his Graph PowerShell session.
- **AzureActivity** on `CorrelationId` and actor (`InitiatedBy.user.userPrincipalName` ↔ `Caller`, and `InitiatedBy.user.id` ↔ the `oid` in `Claims_d`) — the directory privilege escalation here precedes the 10:00 ARM role write / storage key-list; same identity, adjacent in time.
- **AADNonInteractiveUserSignInLogs** on the actor UPN / object id — service-principal and token-driven activity (`InitiatedBy.app`) that an interactive-only view misses.
- **IdentityInfo** (UEBA) on `InitiatedBy.user.id` — enrich the actor and each `TargetResources` principal with role, manager, and risk to judge whether a role grant is anomalous.

## 📚 References
- AuditLogs table reference — https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/auditlogs
- Microsoft Graph `directoryAudit` resource (underlying property model) — https://learn.microsoft.com/en-us/graph/api/resources/directoryaudit?view=graph-rest-1.0
- Microsoft Entra audit activity list & monitoring — https://learn.microsoft.com/en-us/entra/identity/monitoring-health/concept-audit-logs
