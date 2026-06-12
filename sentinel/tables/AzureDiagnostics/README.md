# AzureDiagnostics

> **Category:** Azure Monitor — Azure resource logs (multi-service, "Azure Diagnostics mode")
> **Connector / source:** Azure platform **diagnostic settings** on each resource, routed to a Log Analytics workspace. Any Azure service configured in *Azure Diagnostics* mode (rather than resource-specific mode) lands here — e.g. **Key Vault** (`AuditEvent`), **Application Gateway / WAF**, **Network Security Groups** (`NetworkSecurityGroupRuleCounter`, `NetworkSecurityGroupEvent`), **Data Factory**, **API Management**, **Azure Firewall** (legacy), **Cosmos DB**, **Azure SQL**, **Recovery Services**, **Automation**, **Front Door / CDN**, **Service Bus / Event Hub**.
> **Table plan:** Analytics (default). (The reference does not flag a Basic variant; AzureDiagnostics is a workspace-created custom table and cannot be pre-provisioned via ARM/tables API.)
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/azurediagnostics

## What this table is
Each row is one **resource log record** emitted by an Azure service running in *Azure Diagnostics mode*. It is the generic catch-all table for dozens of Azure services that do **not** have (or are not configured to use) a dedicated resource-specific table. Because so many different resource types share it, AzureDiagnostics is a **wide, schema-on-read** table keyed by `ResourceProvider` + `ResourceType` + `Category`: you almost always filter on those first, then read the service-specific columns. Rows appear within minutes of the activity once diagnostic settings are enabled on the resource. In a SOC it is the primary table for **Key Vault secret/key access auditing**, **Application Gateway/WAF and NSG traffic analysis**, **Data Factory / Automation runbook activity**, and **PaaS data-plane forensics** generally — anywhere the dedicated table doesn't exist.

## Schema
Full column list, validated against the Microsoft Learn reference (170 distinct columns; the page renders `ResourceProvider`, `ResourceType`, `ResultType`, and `ResultDescription` twice — listed once here). Service-specific fields use Log Analytics **type suffixes** (see gotchas): `_s` string, `_d` double, `_b` bool, `_g` guid, `_t` datetime. Types below are the KQL/Log Analytics types.

### Common envelope columns (present for most resource types)
| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | UTC time the record was generated (always filter this first). |
| ResourceProvider | string | The Azure resource provider namespace, e.g. `MICROSOFT.KEYVAULT`, `MICROSOFT.NETWORK`, `MICROSOFT.DATAFACTORY`. **Primary routing column.** |
| ResourceType | string | The resource type within the provider, e.g. `VAULTS`, `NETWORKSECURITYGROUPS`, `APPLICATIONGATEWAYS`, `FACTORIES`. **Primary routing column.** |
| Category | string | The diagnostic log category, e.g. `AuditEvent` (Key Vault), `NetworkSecurityGroupEvent`, `ApplicationGatewayAccessLog`, `PipelineRuns`. **Primary routing column.** |
| OperationName | string | The operation that produced the record, e.g. `SecretGet`, `KeyGet`, `VaultGet`, `NetworkSecurityGroupCounters`, `Microsoft.DataFactory/factories/pipelineruns/read`. |
| OperationVersion | string | API version associated with `OperationName`. |
| ResultType | string | Operation outcome — a **string** (e.g. `Success`, `Failed`), not an int. |
| ResultSignature | string | Service-specific result detail, often an HTTP status (e.g. `OK`, `200`, `Forbidden`). |
| ResultDescription | string | Free-text description of the result. |
| Resource | string | The resource name (e.g. `KV-CONTOSO-PROD`) — note Azure upper-cases this. |
| ResourceGroup | string | Resource group name (e.g. `RG-FINANCE-PROD`). |
| ResourceId / _ResourceId | string | The full ARM resource ID. `_ResourceId` is the standard Azure Monitor identifier for the resource the record is associated with. |
| SubscriptionId | guid | Subscription GUID (surfaced via the resource ID; standard Azure Monitor column). |
| CallerIPAddress | string | Source IP of the API caller (Key Vault, ARM-style data-plane ops). **Primary network column.** |
| Caller_s | string | The caller principal (UPN / object id / app id) for some providers. |
| callerId_s | string | Alternate caller identifier (e.g. Data Factory). |
| CorrelationId | string | Correlation/request id used to stitch related operations together. |
| Level | string | Severity level (`Informational`, `Warning`, `Error`). |
| Message | string | Free-text message payload (where the service emits one). |
| DurationMs | long | Operation duration in milliseconds. |
| Region_s | string | Azure region of the resource. |
| Environment_s | string | Service environment tag. |
| Type | string | The table name (`AzureDiagnostics`). |
| **AdditionalFields** | dynamic | **Property bag.** When the workspace's AzureDiagnostics table reaches the 500-column limit, *any new* service field is written here as JSON instead of getting its own column. Extract with dynamic operators (`AdditionalFields.<name>`) and **typecast** before use. |

### Identity / claim columns (Key Vault & token-based providers)
| Column | Type | Description |
|---|---|---|
| identity_claim_appid_g | guid | App registration (client) ID from the caller's token — Key Vault `AuditEvent`. |
| identity_claim_ipaddr_s | string | Caller IP carried inside the identity claim (Key Vault). |
| isAccessPolicyMatch_b | bool | Whether the Key Vault access policy matched the request (legacy vault-access-policy model). |
| server_principal_sid_s | string | SID of the server principal (Azure SQL audit). |
| database_principal_name_s | string | Database principal that performed the action (Azure SQL audit). |

### HTTP / request columns (Key Vault, App Gateway, API Management, Cosmos DB)
| Column | Type | Description |
|---|---|---|
| requestUri_s | string | The request URI of the data-plane call (e.g. the Key Vault secret URL, App Gateway request). |
| httpMethod_s | string | HTTP method (`GET`, `PUT`, `DELETE`, …). |
| httpStatusCode_d | double | HTTP status code as a number (Key Vault, App Gateway). |
| httpStatusCode_s | string | HTTP status code as a string (some providers). |
| httpStatus_d | double | HTTP status (Cosmos DB / other). |
| httpVersion_s | string | HTTP protocol version. |
| requestQuery_s | string | Request query string. |
| requestResourceId_s | string | Target resource id of the request. |
| requestResourceType_s | string | Target resource type of the request. |
| clientInfo_s | string | Client / user-agent info string (Key Vault). |
| clientIP_s / clientIp_s / client_ip_s / clientIpAddress_s | string | Client source IP variants used by different providers (App Gateway, Cosmos DB, API Management). |
| clientPort_d | double | Client source port. |
| code_s | string | Provider-specific result/error code. |
| id_s | string | Provider-specific record/operation id (Key Vault audit record id). |
| resultCode_s | string | Provider result code. |
| resultMessage_s | string | Provider result message. |
| receivedBytes_d | double | Bytes received (App Gateway / network). |
| sentBytes_d | double | Bytes sent (App Gateway / network). |
| backendHostname_s | string | Backend host the request was routed to (App Gateway). |
| routingRuleName_s | string | App Gateway routing rule name. |
| ruleName_s | string | Matched rule name (NSG / WAF / App Gateway). |
| host_s | string | Host header / hostname. |
| error_code_s | string | Error code. |
| error_message_s | string | Error message. |
| errorLevel_s | string | Error level. |

### Network Security Group columns (`MICROSOFT.NETWORK` / NSG categories)
| Column | Type | Description |
|---|---|---|
| direction_s | string | Rule direction (`In` / `Out`). |
| priority_d | double | NSG rule priority. |
| conditions_sourceIP_s | string | Source IP/CIDR condition of the matched rule. |
| conditions_destinationIP_s | string | Destination IP/CIDR condition. |
| conditions_sourcePortRange_s | string | Source port range condition. |
| conditions_destinationPortRange_s | string | Destination port range condition. |
| conditions_protocols_s | string | Protocol condition (`TCP`/`UDP`/`*`). |
| conditions_None_s | string | Catch-all condition field. |
| matchedConnections_d | double | Number of connections matched by the NSG rule counter. |
| primaryIPv4Address_s | string | Primary IPv4 address of the NIC/endpoint. |
| macAddress_s | string | MAC address of the interface. |
| ip_s | string | Generic IP field (provider-dependent). |
| policy_s | string | Policy name. |
| policyMode_s | string | Policy mode (e.g. WAF `Detection`/`Prevention`). |

### Key Vault property columns
| Column | Type | Description |
|---|---|---|
| properties_enabledForDeployment_b | bool | Vault enabled for VM deployment secret retrieval. |
| properties_enabledForDiskEncryption_b | bool | Vault enabled for Azure Disk Encryption. |
| properties_enabledForTemplateDeployment_b | bool | Vault enabled for ARM template deployment. |
| properties_tenantId_g | guid | Tenant ID associated with the vault. |
| properties_sku_Family_s | string | Vault SKU family. |
| properties_sku_Name_s | string | Vault SKU name (`standard`/`premium`). |
| properties_s | string | Serialized properties blob (string, not dynamic). |

### Data Factory / Automation / runbook columns
| Column | Type | Description |
|---|---|---|
| resource_runId_s | string | Data Factory pipeline run ID. |
| resource_originRunId_s | string | Origin run ID for re-runs. |
| resource_pipelineName / resource_workflowName_s | string | Pipeline / workflow name. |
| resource_workflowId_g | guid | Workflow (pipeline) GUID. |
| resource_triggerName_s | string | Trigger that started the run. |
| resource_actionName_s | string | Action name. |
| resource_resourceGroupName_s | string | Resource group of the DF resource. |
| resource_subscriptionId_g | guid | Subscription of the DF resource. |
| resource_location_s | string | Location of the DF resource. |
| RunbookName_s | string | Automation runbook name. |
| RunOn_s | string | Hybrid worker / Azure target the runbook ran on. |
| JobId_g / jobId_s / JobUniqueId_g | guid/string | Automation/backup job identifiers. |
| JobStatus_s | string | Job status (`Completed`/`Failed`). |
| JobOperation_s / JobOperationSubType_s | string | Job operation and sub-type (Recovery Services). |
| JobFailureCode_s | string | Job failure code. |
| JobStartDateTime_s | string | Job start time (**string**, despite the time semantics). |
| JobDurationInSecs_s | string | Job duration in seconds (**string**). |
| AdHocOrScheduledJob_s | string | Whether the job was ad-hoc or scheduled. |
| instanceId_s | string | Instance id. |
| EventName_s | string | Event name. |
| event_s / event_class_s / event_subclass_s | string | Event classification fields (Analysis Services / SQL). |
| event_time_t / endTime_t / executionInfo_startTime_t / executionInfo_endTime_t | datetime | Event/execution timestamps (note `_t` suffix = datetime). |
| executionInfo_exitCode_d | double | Execution exit code. |

> **Plus ~90 standard numeric/string columns** carried for **Azure SQL, Cosmos DB, and performance** scenarios — e.g. `query_hash_s`, `query_plan_hash_s`, `querytext_s`, `query_id_d`, `cpu_time_d`, `duration_d`, `duration_milliseconds_d`, `logical_io_reads_d`, `logical_io_writes_d`, `physical_io_reads_d`, `num_physical_io_reads_d`, `log_bytes_used_d`, `query_max_used_memory_d`, `response_rows_d`, `rowcount_d`, `dop_d`, `session_id_d`, `object_id_d`, `object_name_s`, `schema_name_s`, `database_name_s`, `DatabaseName_s`, `LogicalServerName_s`, `ElasticPoolName_s`, `partitionKey_s`, `collectionName_s`, `db_id_s`, `requestCharge_s`, `application_name_s`, `audit_schema_version_d`, `action_id_s`/`action_name_s`/`action_s`, `is_column_permission_s`, `statement_s`, plus their `avg_`/`max_`/`min_`/`count_`/`interval_` aggregate variants. These are not security-relevant for the scenario below and are omitted individually; **none are invented** — all appear on the reference page. The full authoritative list is the Microsoft Learn page linked above.

## Key columns for detection & hunting
- **Routing (always filter first):** `ResourceProvider`, `ResourceType`, `Category` — this table is useless without narrowing to a service. Then `OperationName` for the specific action.
- **Identity:** No single canonical identity column — it is provider-specific. Key Vault: `identity_claim_appid_g` (app/client id) and the caller carried in `Caller_s` / token claims; Data Factory: `callerId_s`; SQL: `database_principal_name_s` / `server_principal_sid_s`. The *human* UPN often is **not** present (token apps) — pivot to `SigninLogs`/`AADNonInteractiveUserSignInLogs` via IP and app id.
- **Host / device:** n/a in the Windows-hostname sense. `backendHostname_s` (App Gateway backend), `host_s`, `primaryIPv4Address_s` / `macAddress_s` (NSG interface).
- **Network:** `CallerIPAddress` (Key Vault / ARM data-plane), `identity_claim_ipaddr_s` (Key Vault token claim), `clientIP_s`/`clientIp_s`/`client_ip_s`/`clientIpAddress_s` (App Gateway, Cosmos, APIM), NSG `conditions_sourceIP_s` / `conditions_destinationIP_s`.
- **Outcome / result:** `ResultType` (**string** — `Success`/`Failed`), `ResultSignature` (often the HTTP status), `httpStatusCode_d` (numeric), `resultCode_s`. Always treat `ResultType` as a string.
- **Timestamps:** `TimeGenerated` (UTC, primary). Service event-times use the `_t` suffix (e.g. `event_time_t`, `endTime_t`).
- **Join keys (to other tables):** `CorrelationId` (↔ `AzureActivity.CorrelationId` for the control-plane twin of a data-plane event), `CallerIPAddress` / `identity_claim_ipaddr_s` (↔ `SigninLogs.IPAddress`, `CommonSecurityLog`), `identity_claim_appid_g` (↔ `AADServicePrincipalSignInLogs.AppId` / `SigninLogs.AppId`), `_ResourceId` (↔ `AzureActivity`, `AzureMetrics`), `SubscriptionId` / `ResourceGroup` (scope correlation).

## ⚠️ Schema gotchas
- **Type suffixes are part of the column name.** A field's name encodes its type: `_s` = string, `_d` = double, `_b` = bool, `_g` = guid, `_t` = datetime. So the *same* logical value can exist as both `httpStatusCode_d` (number) and `httpStatusCode_s` (string) depending on the emitting service — reference the exact suffixed name and don't assume a numeric `_d` twin exists.
- **Always filter `ResourceProvider`/`ResourceType`/`Category` first.** It is a multi-resource table; an un-narrowed query scans every Azure service's logs and most columns will be null for any given row. Microsoft explicitly recommends a `ResourceType` filter immediately after the `TimeGenerated` filter.
- **`AdditionalFields` is where new fields go after the 500-column cap.** Once the workspace's AzureDiagnostics table hits 500 columns, *new* service properties stop getting their own column and are appended to the `AdditionalFields` dynamic property bag. A field you expect as `Foo_s` may instead be `AdditionalFields.Foo` — and you **must typecast** (`tostring(...)`, `toint(...)`) before operating on it. Filtering `AdditionalFields has "Foo"` is cheaper than parsing at high volume.
- **`ResultType` is a string, not an int/bool.** Filter `== "Success"` / `== "Failed"`. `ResultSignature` often carries the HTTP outcome (`OK`, `Forbidden`, `200`) — also a string.
- **Identity is not uniform.** There is no single `UserPrincipalName`/`Identity` column across providers; many records (especially Key Vault data-plane from service principals) carry only an **app id** (`identity_claim_appid_g`) and an **IP** — correlate out to sign-in logs to resolve who acted.
- **`Resource`, `ResourceGroup` values are upper-cased by Azure.** `Resource == "KV-CONTOSO-PROD"`, not `kv-contoso-prod`. Use `=~` (case-insensitive) when matching against names from other tables.
- **Prefer the resource-specific table when one exists.** Many services (Key Vault `AZKVAuditLogs`, App Gateway `AGWAccessLogs`/`AGWFirewallLogs`, NSG flow `AZFWNetworkRule`/flow-logs in `NTANetAnalytics`, Data Factory `ADFActivityRun`) now support *resource-specific* mode and won't appear here at all when that mode is selected — confirm which mode the diagnostic setting uses before building a detection.

## 🧪 Sample data
[`AzureDiagnostics_sample.csv`](AzureDiagnostics_sample.csv) — 24 rows. Compromised finance analyst **alexw** (and the abused **svc-backup** service principal), driven from the attacker IP `185.220.101.2`, enumerate and pull secrets/keys from Key Vault `kv-contoso-prod` after a privilege grant, while an attacker-permissive **NSG rule** is added — amid benign Key Vault reads by legitimate admin **dvora** and routine vault metadata calls.
The sample uses this curated subset of **real** columns: `TimeGenerated`, `ResourceProvider`, `ResourceType`, `Category`, `OperationName`, `ResultType`, `ResultSignature`, `CallerIPAddress`, `identity_claim_appid_g`, `identity_claim_ipaddr_s`, `requestUri_s`, `id_s`, `httpStatusCode_d`, `clientInfo_s`, `CorrelationId`, `Resource`, `ResourceGroup`, `SubscriptionId`, `ruleName_s`, `direction_s`, `conditions_sourceIP_s`, `conditions_destinationPortRange_s`. This is the **Key Vault secrets-access + NSG-rule** step (~10:40) of "Operation Quiet Ledger": the data-plane secret theft that follows the Azure role write (in `AzureActivity`) and feeds the AKS secret-read step.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · Key Vault secret/key harvesting after a role grant — [T1555.006](https://attack.mitre.org/techniques/T1555/006/)
**Hypothesis:** A principal reads an abnormal number of distinct secrets/keys from a production vault in a short window — bulk credential theft from Key Vault.
```kusto
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.KEYVAULT" and Category == "AuditEvent"
| where OperationName in ("SecretGet", "KeyGet", "CertificateGet", "SecretList", "KeyList")
| where ResultType == "Success"
| extend CallerIP = coalesce(CallerIPAddress, identity_claim_ipaddr_s)
| summarize Reads = count(), Secrets = make_set(requestUri_s, 25),
            FirstSeen = min(TimeGenerated), LastSeen = max(TimeGenerated)
          by Resource, AppId = tostring(identity_claim_appid_g), CallerIP, bin(TimeGenerated, 15m)
| where Reads >= 3
| sort by Reads desc
```
**Triage:** True positive = many distinct `SecretGet`/`KeyGet` from one principal + foreign IP minutes after a role/policy change (`185.220.101.2` against `KV-CONTOSO-PROD`). Benign = an app or `svc-backup` reading its *own* known secret on a schedule from a corporate IP.

### H2 · Key Vault access from a suspicious / external IP — [T1078.004](https://attack.mitre.org/techniques/T1078/004/)
**Hypothesis:** Vault data-plane operations originate from an IP that is not normal corporate egress (valid cloud account abused from attacker infrastructure).
```kusto
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.KEYVAULT" and Category == "AuditEvent"
| extend CallerIP = coalesce(CallerIPAddress, identity_claim_ipaddr_s)
| where isnotempty(CallerIP)
| where CallerIP !startswith "52.170." and CallerIP !startswith "20.98."   // known corp egress
| project TimeGenerated, Resource, OperationName, ResultType, ResultSignature, CallerIP,
          AppId = tostring(identity_claim_appid_g), requestUri_s, clientInfo_s
| sort by TimeGenerated asc
```
**Triage:** True positive = `kv-contoso-prod` accessed from `185.220.101.2` (NL) by `alexw`/`svc-backup`. Benign = a new but legitimate Azure region/egress IP — confirm against the app's expected source ranges.

### H3 · Permissive NSG rule added / counted (network exposure) — [T1562.007](https://attack.mitre.org/techniques/T1562/007/)
**Hypothesis:** An inbound NSG rule allows traffic from a wide/untrusted source to a sensitive management port (e.g. RDP 3389, SSH 22) — defense weakening to keep access.
```kusto
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.NETWORK" and ResourceType == "NETWORKSECURITYGROUPS"
| where direction_s == "In"
| where conditions_destinationPortRange_s in ("3389", "22", "*")
| where conditions_sourceIP_s in ("*", "0.0.0.0/0") or conditions_sourceIP_s startswith "185.220."
| project TimeGenerated, Resource, ResourceGroup, ruleName_s, direction_s,
          conditions_sourceIP_s, conditions_destinationPortRange_s, OperationName
| sort by TimeGenerated asc
```
**Triage:** True positive = a newly-counted rule like `AllowAnyRDPInbound` opening 3389 to `*` on `RG-FINANCE-PROD` infrastructure. Benign = an existing, documented management rule scoped to a bastion subnet.

### H4 · Failed vault access bursts (enumeration / brute) — [T1580](https://attack.mitre.org/techniques/T1580/)
**Hypothesis:** A principal generates repeated `Forbidden`/`Failed` vault operations before a success — probing access scope after landing.
```kusto
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.KEYVAULT" and Category == "AuditEvent"
| extend CallerIP = coalesce(CallerIPAddress, identity_claim_ipaddr_s)
| summarize Failures = countif(ResultType == "Failed"),
            Successes = countif(ResultType == "Success"),
            Ops = make_set(OperationName, 15)
          by Resource, AppId = tostring(identity_claim_appid_g), CallerIP, bin(TimeGenerated, 10m)
| where Failures >= 2 and Successes >= 1
| sort by Failures desc
```
**Triage:** True positive = several `Forbidden` reads then a `Success` once a role/policy is granted (the privilege-escalation signature). Benign = a misconfigured app retrying against the wrong vault.

## 🔗 Correlates with
- **AzureActivity** on `CorrelationId` and `_ResourceId` — the **control-plane twin**: the `Microsoft.Authorization/roleAssignments/write` (role grant) and `Microsoft.KeyVault/vaults/write` / NSG `securityRules/write` that *enabled* the data-plane access seen here.
- **SigninLogs / AADServicePrincipalSignInLogs** on `identity_claim_ipaddr_s` ↔ `IPAddress` and `identity_claim_appid_g` ↔ `AppId` — resolve the *human/service identity* and risk state behind a Key Vault caller that only logged an app id + IP.
- **AzureNetworkAnalytics_CL / NTANetAnalytics / CommonSecurityLog** on the NSG `Resource` and IP conditions — see whether the permissive rule actually carried attacker traffic.
- **AKSAudit / AzureDiagnostics (kube-audit)** on `Resource`/secret name — tie the stolen Key Vault secret to the subsequent AKS secret-read / `exec` step of the same intrusion.

## 📚 References
- [AzureDiagnostics table reference — Microsoft Learn](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/azurediagnostics)
- [Azure resource logs — diagnostics mode vs resource-specific mode — Microsoft Learn](https://learn.microsoft.com/en-us/azure/azure-monitor/platform/resource-logs)
- [Azure Key Vault logging — Microsoft Learn](https://learn.microsoft.com/en-us/azure/key-vault/general/logging)
- [Monitoring NSGs / diagnostic logs — Microsoft Learn](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-nsg-manage-log)
