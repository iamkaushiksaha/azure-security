# AzureActivity

> **Category:** Azure Activity (Azure Resources, Audit, Security)
> **Connector / source:** Azure Activity log → the "Azure Activity" data connector in Microsoft Sentinel (modern path is a diagnostic-setting / DCR pipeline from the subscription Activity log; legacy path was the Log Analytics agent "Azure Activity log" connector). Subscription- and management-group-level control-plane events from Azure Resource Manager.
> **Table plan:** Analytics (default). The reference flags **Basic log: No** and **Ingestion-time DCR support: No**, so Basic/Auxiliary plans and ingestion-time transforms are not available for this table.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/azureactivity

## What this table is
Each row is a single **control-plane** event from the Azure Activity log — a write/action/delete (or its outcome) performed through Azure Resource Manager (ARM) against a subscription, resource group, or resource. Rows appear within minutes of any management operation: creating/deleting resources, assigning RBAC roles, listing storage keys, editing NSG rules, reading Key Vault, deploying templates, changing policy. It captures **who** (`Caller`), **from where** (`CallerIpAddress`), **what** (`OperationNameValue`), and **outcome** (`ActivityStatusValue`) — but never the *data-plane* (no blob GETs, no secret values; those live in resource-specific diagnostic logs such as `StorageBlobLogs` / `AzureDiagnostics`). In a SOC it is the primary table for **Azure privilege escalation and resource-abuse detection**: anomalous `roleAssignments/write`, `listKeys`/`listAccountSas` credential theft, NSG/firewall rule tampering, and Key Vault access-policy changes.

## Schema
Full column list, validated against the Microsoft Learn reference. Types are the KQL/Log Analytics types. Dynamic (nested JSON) columns are marked **dyn**.

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | When the Azure service processing the request generated the event (event time, UTC). |
| ActivityStatus | string | **Legacy** raw status string. Prefer `ActivityStatusValue`. |
| ActivityStatusValue | string | Status of the operation, display-friendly. Common values: `Started`, `In Progress`, `Succeeded`, `Failed`, `Active`, `Resolved`. |
| ActivitySubstatus | string | **Legacy** raw substatus string. Prefer `ActivitySubstatusValue`. |
| ActivitySubstatusValue | string | Substatus, display-friendly, e.g. `OK (HTTP Status Code: 200)`, `Forbidden (HTTP Status Code: 403)`. |
| Authorization | string | **Legacy** RBAC blob (string): `action`, `role`, `scope`. Prefer `Authorization_d`. |
| Authorization_d | **dyn** | RBAC properties of the event as dynamic: usually `action`, `role`, `scope` (and `evidence` for role-based grants). The detail used to attribute *what right* was exercised. |
| Caller | string | The actor: a **UPN** for a user (`alexw@contoso.com`) or a **service-principal GUID** for an app/managed identity. (Page labels it "GUID of the caller", but it holds the UPN/SPN claim.) |
| CallerIpAddress | string | Source IP address of the caller that performed the operation. |
| Category | string | **Legacy** raw category. Prefer `CategoryValue`. |
| CategoryValue | string | Activity-log category, e.g. `Administrative`, `Policy`, `Security`, `ServiceHealth`, `Autoscale`, `Recommendation`. |
| Claims | string | **Legacy** JWT/claims string used to authenticate the caller to ARM. Prefer `Claims_d`. |
| Claims_d | **dyn** | Claims from the JWT used by Entra ID to authenticate the caller — incl. `appid`, `ipaddr`, `puid`, `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name` (UPN), object id (`oid`). |
| CorrelationId | string | GUID; events sharing a `CorrelationId` belong to the same uber-action (key cross-table join). |
| EventDataId | string | Unique identifier of an individual event. |
| EventSubmissionTimestamp | datetime | When the event became available for querying (ingestion time). |
| Hierarchy | string | Management-group hierarchy of the MG/subscription the event belongs to. |
| HTTPRequest | string | Blob describing the HTTP request: `clientRequestId`, `clientIpAddress`, `method` (e.g. `PUT`). |
| Level | string | Event level: `Critical`, `Error`, `Warning`, `Informational`, `Verbose`. |
| OperationId | string | GUID of the operation. |
| OperationName | string | **Legacy** localized/raw operation name. Prefer `OperationNameValue`. |
| OperationNameValue | string | Operation identifier, e.g. `Microsoft.Authorization/roleAssignments/write`, `Microsoft.Storage/storageAccounts/listKeys/action`. The primary "what happened" field. |
| Properties | string | **Legacy** key/value detail blob (string). Prefer `Properties_d`. |
| Properties_d | **dyn** | Event detail as dynamic: e.g. `entity` (assignment id), `message`, `requestbody`, `hierarchy`, `eventCategory`, `statusCode`. Holds the deepest forensic detail. |
| Resource | string | Name of the impacted resource (short name). |
| ResourceGroup | string | Resource-group name of the impacted resource. |
| ResourceId | string | **Legacy** resource id. Prefer `_ResourceId`. |
| _ResourceId | string | Full ARM resource id of the impacted resource. |
| ResourceProvider | string | **Legacy** raw resource-provider field. Prefer `ResourceProviderValue`. |
| ResourceProviderValue | string | Resource provider of the impacted resource, e.g. `Microsoft.Storage`, `Microsoft.Authorization`, `Microsoft.Network`. |
| SubscriptionId | string | Subscription ID of the impacted resource. |
| _SubscriptionId | string | Unique identifier for the subscription the record is associated with. |
| SourceSystem | string | Collecting agent type; `Azure` for Azure-emitted records. |
| TenantId | string | The Log Analytics **workspace** ID (not the Entra tenant — see gotchas). |
| Type | string | Table name (`AzureActivity`). |

> **38 columns** total on the reference. Above lists every detection-relevant column individually. Trailing platform/billing columns are standard: `_BilledSize` (real), `_IsBillable` (string).

## Key columns for detection & hunting
- **Identity:** `Caller` — UPN for users, SPN **GUID** for apps/managed identities. Deeper claims (appid, oid, ipaddr, name) live in `Claims_d`; parse with `parse_json(Claims_d)`.
- **Host / device:** n/a — this is ARM control-plane, there is no source hostname. `CallerIpAddress` is the only locator.
- **Network:** `CallerIpAddress` (source IP of the caller); `clientIpAddress` is also echoed inside `HTTPRequest` / `Claims_d.ipaddr`.
- **Outcome / result:** `ActivityStatusValue` (**string**: `Started` → `Succeeded`/`Failed`) plus `ActivitySubstatusValue` (carries the HTTP code, e.g. `Forbidden (HTTP Status Code: 403)`). A write typically logs a `Started` row then a `Succeeded`/`Failed` row sharing `CorrelationId`/`OperationId`.
- **Timestamps:** `TimeGenerated` (event time) and `EventSubmissionTimestamp` (ingestion time).
- **Join keys (to other tables):** `Caller` (UPN → `SigninLogs`/`AuditLogs`/`OfficeActivity`), `CallerIpAddress` (→ any network/threat-intel table or `SigninLogs.IPAddress`), `CorrelationId` (→ `AuditLogs`/`AzureDiagnostics` for the same uber-action), `SubscriptionId` / `ResourceGroup` / `_ResourceId` (→ resource-specific logs like `StorageBlobLogs`).

## ⚠️ Schema gotchas
- **Outcome is a STRING, in the `*Value` columns.** Filter `ActivityStatusValue == "Failed"` (string), not a bool/int. The bare `ActivityStatus`/`ActivitySubstatus`/`Category`/`OperationName`/`ResourceProvider` columns are the **legacy raw twins** — for every one of these, the `…Value` column is the one you query. Building dashboards on the non-`Value` twins is the classic mistake.
- **Prefer the `_d` dynamic columns over the legacy string blobs.** `Authorization_d`, `Claims_d`, `Properties_d` are real `dynamic` (index/extract directly: `Authorization_d.action`, `tostring(Claims_d.appid)`). The same-named `Authorization`/`Claims`/`Properties` are deprecated strings; if you must read them, `parse_json()` first.
- **`Caller` is not always a UPN.** For automation, managed identities, and app principals it is a **GUID** (the service-principal object id). A hunt that assumes `Caller contains "@"` will miss all service-principal activity (e.g. `svc-backup`). Use `Claims_d.appid` to resolve the app.
- **`TenantId` here = the Log Analytics workspace ID**, not the Entra tenant. The Entra tenant / actor ids live inside `Claims_d` (`tid`, `oid`). Don't join `AzureActivity.TenantId` to `SigninLogs.AADTenantId`.
- **A successful write usually produces ≥2 rows** (`Started` then `Succeeded`) sharing `CorrelationId`/`OperationId`. Count `distinct OperationId` (or filter `ActivityStatusValue == "Succeeded"`) when counting *operations*, or you will double-count.

## 🧪 Sample data
[`AzureActivity_sample.csv`](AzureActivity_sample.csv) — 24 rows. Tells the **Operation Quiet Ledger** Azure-pivot step (~10:00): the compromised `alexw@contoso.com` and the abused service principal `svc-backup` (GUID caller) operate from attacker IPs `185.220.101.2` / `91.219.236.18` to (1) write a `roleAssignments` granting **Owner/Contributor on rg-finance-prod** (`Microsoft.Authorization/roleAssignments/write`), (2) call `Microsoft.Storage/storageAccounts/listKeys/action` on **stcontosofin** to steal access keys for blob exfil, and (3) write an NSG security rule opening egress (`Microsoft.Network/networkSecurityGroups/securityRules/write`) — plus a Key Vault access-policy change on `kv-contoso-prod`. These sit amid benign deployments by `dvora@contoso.com` and `itadmin@contoso.com` (resource group / VM / storage writes from corporate egress `52.170.12.45` / `20.98.111.30`). This is the **10:00 Azure role-write + storage-key-list** step, downstream of the 08:20 risky sign-in (`SigninLogs`) and feeding the 10:20 blob exfil.

The sample uses this curated subset of **real** columns: `TimeGenerated`, `Caller`, `CallerIpAddress`, `OperationNameValue`, `ActivityStatusValue`, `ActivitySubstatusValue`, `CategoryValue`, `Level`, `ResourceGroup`, `Resource`, `_ResourceId`, `ResourceProviderValue`, `SubscriptionId`, `CorrelationId`, `Authorization_d`, `Claims_d`, `Properties_d`.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · RBAC privilege escalation — role assignment written — [T1098.003](https://attack.mitre.org/techniques/T1098/003/)
**Hypothesis:** A caller writes a role assignment granting a high-privilege role (`Owner` / `Contributor` / `User Access Administrator`), especially scoped to a sensitive resource group — privilege escalation / persistence.
```kusto
AzureActivity
| where OperationNameValue == "Microsoft.Authorization/roleAssignments/write"
| where ActivityStatusValue == "Succeeded"
| extend Role  = tostring(Authorization_d.evidence.role)
| extend Scope = tostring(Authorization_d.scope)
| where Role in ("Owner", "Contributor", "User Access Administrator")
| project TimeGenerated, Caller, CallerIpAddress, Role, Scope, ResourceGroup, CorrelationId
| order by TimeGenerated asc
```
**Triage:** True positive = a finance analyst / service principal granting itself Owner on `rg-finance-prod` from a non-corporate IP (`185.220.101.2`). Benign = `itadmin`/`dvora` performing expected grants from corporate egress during a change window.

### H2 · Storage key / SAS theft — [T1552.005](https://attack.mitre.org/techniques/T1552/005/)
**Hypothesis:** A caller invokes `listKeys` or `listAccountSas` on a storage account to harvest long-lived credentials for data-plane exfiltration.
```kusto
AzureActivity
| where OperationNameValue in (
    "Microsoft.Storage/storageAccounts/listKeys/action",
    "Microsoft.Storage/storageAccounts/listAccountSas/action")
| where ActivityStatusValue == "Succeeded"
| project TimeGenerated, Caller, CallerIpAddress, OperationNameValue,
          Resource, ResourceGroup, _ResourceId, CorrelationId
| order by TimeGenerated asc
```
**Triage:** True positive = `listKeys` on `stcontosofin` from the attacker IP minutes after a role write, by a caller that doesn't normally touch storage. Benign = a known backup/automation SPN listing keys on a schedule from a stable IP.

### H3 · Network security-rule tampering (egress opened) — [T1562.007](https://attack.mitre.org/techniques/T1562/007/)
**Hypothesis:** A caller writes or deletes an NSG security rule (or Azure Firewall rule), potentially opening egress for exfil/C2 or disabling a control.
```kusto
AzureActivity
| where OperationNameValue has_any (
    "networkSecurityGroups/securityRules/write",
    "networkSecurityGroups/securityRules/delete",
    "azureFirewalls/write")
| where ActivityStatusValue in ("Succeeded", "Started")
| project TimeGenerated, Caller, CallerIpAddress, OperationNameValue,
          Resource, ResourceGroup, ActivityStatusValue, CorrelationId
| order by TimeGenerated asc
```
**Triage:** True positive = a rule allowing broad outbound `*` written by the compromised user right before exfil. Benign = a network admin's reviewed change, correlated to a change ticket / corporate IP.

### H4 · Operations from a single attacker IP across providers — [T1078.004](https://attack.mitre.org/techniques/T1078/004/)
**Hypothesis:** One `CallerIpAddress` drives sensitive operations across multiple resource providers in a short window — a hands-on-keyboard cloud session rather than scoped automation.
```kusto
AzureActivity
| where CallerIpAddress in ("185.220.101.2", "91.219.236.18")
| summarize Ops = make_set(OperationNameValue), Providers = make_set(ResourceProviderValue),
            Callers = make_set(Caller), n = count()
            by CallerIpAddress, bin(TimeGenerated, 30m)
| where array_length(Providers) >= 2
| order by n desc
```
**Triage:** True positive = `Authorization` + `Storage` + `Network` + `KeyVault` providers all touched from one foreign IP within 30 min. Benign = a deployment pipeline IP hitting many providers but from known egress and with `Succeeded` template deployments only.

## 🔗 Correlates with
- **SigninLogs** on `Caller` (= UPN) and `CallerIpAddress` (= `IPAddress`) — tie the 10:00 Azure operations back to the 08:20 risky interactive sign-in of the same compromised identity / IP.
- **AuditLogs** on `CorrelationId` (and the UPN) — the Entra-side directory changes (group/role adds) that often pair with ARM `roleAssignments/write` in the same uber-action.
- **StorageBlobLogs / AzureDiagnostics** on `_ResourceId` / `SubscriptionId` — the data-plane follow-through (blob reads, secret gets) after `listKeys` succeeds here; control-plane key-list then data-plane exfil.
- **OfficeActivity** on `Caller` (UPN) — the same actor's M365 activity for the wider compromise timeline.

## 📚 References
- AzureActivity table reference — https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/azureactivity
- Azure Activity log connector for Microsoft Sentinel — https://learn.microsoft.com/en-us/azure/sentinel/data-connectors/azure-activity
- Azure built-in roles (Owner/Contributor/UAA) — https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles
