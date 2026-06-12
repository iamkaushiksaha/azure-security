# DnsAuditEvents

> **Category:** Security (Microsoft Sentinel — Windows DNS Server audit channel)
> **Connector / source:** Windows DNS Server audit events, collected by the **Microsoft Sentinel "Windows DNS Server" / DNS connector** (AMA DCR or the legacy MMA/Log Analytics agent on the DNS server). Populated from the Windows DNS Server **Audit** ETW channel, not the Analytic/query channel.
> **Table plan:** Basic supported — the reference flags **Basic log: Yes** (also lake-only ingestion and ingestion-time DCR support). Defaults to Analytics unless the workspace explicitly sets the table to Basic.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/dnsauditevents

## What this table is
Each row is a **DNS server administrative / change-tracking event** raised by a Windows DNS Server when its **server, zone, or resource-record settings change** — for example a record being added, modified, or deleted; a zone being created, deleted, or transferred; forwarder/scavenging settings being altered; or DNSSEC key and zone-signing operations. It is the *audit* channel, deliberately separate from `DnsEvents` (the high-volume **query/response and analytic** stream): `DnsAuditEvents` answers "**what changed on the DNS service and what is the new state**", while `DnsEvents` answers "who looked up what". The reference notes it **captures audit events that are not from dynamic updates**, so most rows reflect deliberate (admin, API, or tooling) changes. In a SOC it is the primary source for **DNS-tampering and persistence detection** — rogue record creation that redirects an internal name to attacker infrastructure, malicious forwarder/zone-scope changes that hijack resolution, and deletion of records to disrupt logging or services.

## Schema
Full column list, validated against the Microsoft Learn reference. Types are KQL/Log Analytics types. This is a wide, DNSSEC-heavy schema; the high-value change-tracking columns are listed individually and the large DNSSEC key-management block is grouped at the end.

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | Timestamp (UTC) of when the audit event was generated. |
| EventType | string | Type of DNS event (e.g., zone transfer, dynamic update, DNSSEC signing). The primary "what happened" classifier. |
| EventId | string | Identifier for the underlying Windows DNS event. |
| EventGuid | string | Unique identifier for the specific event. |
| EventString | string | Human-readable description of the event. |
| Action | string | If a query meets the criteria of a policy, the action is the response the policy requires (also used as the add/update/delete verb on record/zone changes). |
| ServerName | string | The DNS server where the policy or exception list is being configured (the acting DNS server for the audit event). |
| Name | string | The domain name or hostname associated with a specific record. |
| NodeName | string | The node name within the DNS zone. |
| Zone | string | The zone related to the activity. |
| ZoneName | string | The name of the DNS zone the event relates to. |
| ZoneFile | string | The name of the zone file. |
| ZoneScope | string | A list of scopes and weights for the zone. |
| ChildZone | string | Name of a child zone. |
| RDATA | string | The data of the resource record that was created, deleted, or scavenged in the DNS zone. |
| TTL | int | Time-to-live for the DNS record (how long it should be cached before discard/refresh). |
| DnsQuery | string | The domain that needs to be resolved. |
| DnsQueryType | int | DNS resource-record type code as defined by IANA (e.g., 1=A, 5=CNAME, 6=SOA, 28=AAAA). |
| LookupValue | string | Type of DNS lookup (e.g., recursive, iterative). |
| PropertyKey | string | Specific property or setting affected by the event. |
| OldPropertyValues | string | The set of properties **before** they were updated for a policy/exception list in the DNS server or zone. |
| NewPropertyValues | string | The set of properties **after** they were updated for a policy/exception list in the DNS server or zone. |
| NewValue | string | The updated value assigned to a specific property key within the DNS zone. |
| Setting | string | Specific DNS configuration setting modified by the event. |
| Scope | string | The scope of the event (e.g., server-wide, zone-specific). |
| Scopes | string | DNS scopes impacted by the event (e.g., global, local). |
| RecursionScope | string | Area/conditions under which DNS recursion is allowed or applied on the server. |
| Forwarders | string | DNS forwarders used by the server. |
| MasterServer | string | The primary DNS server from which a secondary obtains zone data. |
| NameServer | string | Name server responsible for the DNS event. |
| ReplicationScope | string | Scope of DNS replication (e.g., forest-wide, domain-specific). |
| Policy | string | Defines rules/guidelines for managing specific aspects of DNS behavior. |
| ProcessingOrder | int | Determines the sequence in which policies are applied. |
| IsEnabled | string | Whether the policy or exception list is currently active. |
| Condition | string | Specific circumstances/requirements that trigger certain actions or policies. |
| Criteria | string | Criteria or conditions that triggered the event. |
| ClientSubnetList | string | The list of IPv4/IPv6 of the client subnet. |
| ClientSubnetRecord | string | The name of the client subnet. |
| FilePath | string | Location of a file/directory the DNS server is interacting with. |
| ScavengeServers | string | Servers involved in DNS scavenging (aging/cleanup of stale records). |
| SubTreeAging | string | Mechanism affecting aging of DNS records within a subtree/branch of a zone. |
| Source | string | Source of the DNS event (e.g., server, client). |
| PropagationTime | int | Time taken for event information to propagate (duration, or "Immediate"). |
| BufferSize | int | Size (bytes) of the buffer used for logging the event data. |
| RolloverType | string | Type of rollover (e.g., overwrite, append). |
| RolloverPeriod | int | Time interval for log rollover. |
| VirtualizationID | string | A unique key to manage/coordinate activities within the virtualized environment. |
| SourceSystem | string | Agent type the event was collected by (`OpsManager` for the Windows agent, `Azure` for Azure Diagnostics). |
| TenantId | string | The Log Analytics workspace ID. |
| Type | string | The name of the table. |
| _ResourceId | string | Unique identifier for the resource the record is associated with. |
| _SubscriptionId | string | Unique identifier for the subscription the record is associated with. |
| _BilledSize | real | The record size in bytes. |
| _IsBillable | string | Whether ingesting the data is billable (string `true`/`false`). |

> **Plus the DNSSEC key-management / zone-signing block (~45 columns, all from the reference):** `Action`-adjacent signing fields including `ActiveKey`, `StandbyKey`, `NextKey`, `KeyId`, `KeyTag`, `KeyType`, `KeyLength`, `KeyProtocol`, `KeyStorageProvider`, `KeyMasterServer`, `IsKeyMasterServer`, `KskOrZsk`, `KeyOrZone`, `WithNewKeys`, `WithWithout`, `CryptoAlgorithm`, `CurrentState`, `CurrentRolloverStatus`, `NextRolloverAction`, `NextRolloverTime` (datetime), `LastRolloverTime` (datetime), `RolloverPeriod`, `InitialRolloverOffset`, `EnableRfc5011KeyRollover`, `SeizedOrTransferred`, `StoreKeysInAD`, `Base64Data`, `Digest`, `DigestType`, `DistributeTrustAnchor`, `DenialOfExistence`, `DnsKeyRecordSetTtl`, `DnsKeySignatureValidityPeriod`, `DSRecordGenerationAlgorithm`, `DSRecordSetTtl`, `DSSignatureValidityPeriod`, `ZoneSignatureValidityPeriod`, `SignatureInceptionOffset`, `SecureDelegationPollingPeriod`, `ParentHasSecureDelegation`, `NSec3HashAlgorithm`, `NSec3Iterations`, `NSec3OptOut`, `NSec3RandomSaltLength`, `NSec3UserSalt`, `ListenAddresses`, `AdditionalData` (dynamic). **Total: ~105 columns.** No column has been invented; `AdditionalData` is the dynamic/nested blob.

## Key columns for detection & hunting
- **Identity (actor):** ⚠️ **none.** This audit channel does **not** carry the calling user/admin who made the change — there is no `Actor`, `Caller`, `Account`, or `InitiatingUser` column. Attribution of *who* changed DNS must come from `SecurityEvent` (4662/5136 on the DC) or `AuditLogs`/`OfficeActivity` correlated by host and time. `ServerName` / `Source` identify the **DNS server**, not the human.
- **Host / device:** `ServerName` (the acting DNS server, e.g. `DC01`); `Name` and `Source` also identify the server; `_ResourceId` carries the full ARM resource path. There is **no `Computer` column** on this table.
- **Network:** No client source-IP column for admin events. The *content* of a change carries IPs as **string data**: `RDATA` / `NewValue` (the record's target address), and `Forwarders` / `MasterServer` / `ListenAddresses` (server-level resolution targets).
- **Outcome / result:** No success/failure code — audit events are emitted for **completed** changes. The semantics live in `EventType` + `EventString` (+ `Action` and the `OldPropertyValues` → `NewPropertyValues` / `NewValue` deltas).
- **Timestamps:** `TimeGenerated` (event time). DNSSEC rollover scheduling via `NextRolloverTime` / `LastRolloverTime`.
- **Join keys (to other tables):** `ServerName` / `Name` → `DeviceName` / `Computer` (`SecurityEvent`, `DeviceEvents`, `DnsEvents`); `Zone` / `ZoneName` → DNS query telemetry in `DnsEvents`; `RDATA` / `NewValue` (the planted IP) → `RemoteIP` / `DestinationIp` in network and logon tables; `_ResourceId` / `_SubscriptionId` → `AzureActivity`.

## ⚠️ Schema gotchas
- **No actor column — you cannot answer "who" from this table alone.** Unlike most audit tables, `DnsAuditEvents` records the *change and the resulting state*, never the calling identity. Treat `ServerName`/`Source` as the **machine**, and pivot to `SecurityEvent` (DC directory-change events 4662/5136) or sign-in/audit tables to attribute the change to `itadmin`/`svc-backup`/etc.
- **No `Computer` column.** Sibling tables (`DnsEvents`, `SecurityEvent`, `Event`) expose `Computer`; here the DNS server lives in **`ServerName` / `Name` / `Source` / `_ResourceId`**. Joins by host must map those instead of `Computer`.
- **`EventId` is a STRING, not an int.** Compare `EventId == "541"`, never a numeric literal. `DnsQueryType` *is* an int (IANA record-type code); don't confuse the two.
- **Audit ≠ analytic. This is not the DNS query stream.** `DnsAuditEvents` holds config/zone/record *changes only* and excludes dynamic updates; lookups, NXDOMAINs, and resolved IPs are in **`DnsEvents`**. Detections that need "host X resolved C2 domain Y" belong against `DnsEvents`, not here.
- **IPs are embedded as strings inside record data.** A malicious redirect shows up as an IP literal in `RDATA` / `NewValue` / `Forwarders` (string fields), not in any typed network column — match with `has`/`contains` / IP-string equality, and remember an attacker can plant either an external or an internal-looking address.
- **Basic-log plan caveat.** The reference flags **Basic log: Yes** (and lake-only ingestion). Under Basic/Auxiliary plans, scheduled-analytics rules and cross-table `join` are restricted — confirm the workspace plan before building alerting on this table.

## 🧪 Sample data
[`DnsAuditEvents_sample.csv`](DnsAuditEvents_sample.csv) — 20 rows. The rows tell the **Operation Quiet Ledger** DNS-tampering step: amid legitimate zone administration on **DC01** (record adds, a new `partners` zone, a forwarder hardening, decommission cleanups by the DNS team), an abused-admin session ~**10:28–11:02** plants attacker-controlled records — `sso`/`vpn`/`autodiscover` pointed at `185.220.101.2` with a **60-second TTL**, a malicious forwarder change to `91.219.236.18`, a rogue external zone scope, a `c2` record — and **deletes the `kv-contoso-prod` record under `_msdcs`** to disrupt Key Vault name resolution.
The sample uses this curated subset of **real** columns: `TimeGenerated`, `EventType`, `EventId`, `EventString`, `Action`, `ServerName`, `Zone`, `ZoneName`, `Name`, `NodeName`, `RDATA`, `NewValue`, `TTL`, `DnsQueryType`, `ReplicationScope`, `Forwarders`, `OldPropertyValues`, `NewPropertyValues`, `Source`, `SourceSystem`. This is the **DNS-tampering / persistence step (~10:30 on DC01)** of the cross-table attack scenario, sitting between the lateral move to DC01 (~09:00–09:40) and the Key Vault / NSG actions (~10:40).

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · Internal name redirected to attacker IP — [T1565.001](https://attack.mitre.org/techniques/T1565/001/)
**Hypothesis:** A record **add or modify** whose `RDATA`/`NewValue` is a non-corporate/external IP, especially with an unusually low TTL, redirects an internal name to attacker infrastructure (data manipulation / spoofing).
```kusto
DnsAuditEvents
| where EventType in ("ResourceRecordCreate", "ResourceRecordSet")
| where Action in ("Add", "Update")
| where RDATA startswith "185.220." or RDATA startswith "91.219." or NewValue startswith "185.220." or NewValue startswith "91.219."
| project TimeGenerated, ServerName, Zone, Name, EventType, Action, RDATA, NewValue, TTL
| sort by TimeGenerated asc
```
**Triage:** True positive = sensitive names (`sso`, `vpn`, `autodiscover`) pointed at `185.220.101.2`/`91.219.236.18` with a 30–60s TTL. Benign = a planned cutover to a known new internal/cloud IP from the corporate range.

### H2 · Malicious forwarder or zone-scope change — resolution hijack — [T1556](https://attack.mitre.org/techniques/T1556/)
**Hypothesis:** A server-level **forwarder** change (or a new external **zone scope**) repoints where the DNS server itself resolves, hijacking resolution org-wide.
```kusto
DnsAuditEvents
| where EventType in ("ServerSettingChange", "ZoneScopeAdd")
| where isnotempty(Forwarders) or ReplicationScope == "External" or NewPropertyValues != OldPropertyValues
| project TimeGenerated, ServerName, EventType, Action, OldPropertyValues, NewPropertyValues, Forwarders, ReplicationScope
| sort by TimeGenerated asc
```
**Triage:** True positive = forwarder moved off the legitimate `168.63.129.16`/internal resolvers to `91.219.236.18`, or an `External` zone scope appears. Benign = approved change to public resolvers (e.g. `8.8.8.8`) inside a change window.

### H3 · Deletion of infrastructure / service records — disruption or defense evasion — [T1485](https://attack.mitre.org/techniques/T1485/)
**Hypothesis:** Deletion of resource records — particularly under `_msdcs` or for security infrastructure — can break service resolution, blind logging, or remove evidence.
```kusto
DnsAuditEvents
| where EventType in ("ResourceRecordDelete", "ZoneDelete")
| where Zone has "_msdcs" or Name has_any ("kv-", "log", "siem", "dc0")
| project TimeGenerated, ServerName, Zone, Name, EventType, Action, RDATA
| sort by TimeGenerated asc
```
**Triage:** True positive = deletion of `kv-contoso-prod` under `_msdcs.contoso.com` mid-incident. Benign = routine decommission cleanup of an end-of-life host record by the DNS team.

### H4 · Low-TTL record churn — fast-flux / agile redirection — [T1568.001](https://attack.mitre.org/techniques/T1568/001/)
**Hypothesis:** Records written with very low TTLs (≤60s) let an attacker re-point a name quickly and minimize cache persistence — atypical for stable internal infrastructure.
```kusto
DnsAuditEvents
| where EventType in ("ResourceRecordCreate", "ResourceRecordSet")
| where TTL <= 60
| project TimeGenerated, ServerName, Zone, Name, RDATA, NewValue, TTL
| sort by TTL asc, TimeGenerated asc
```
**Triage:** True positive = multiple short-TTL records (`sso`, `vpn`, `c2`) added in a tight window. Benign = a deliberately low-TTL record for a load-balanced/failover service documented in change management.

## 🔗 Correlates with
- **SecurityEvent** on `ServerName` → `Computer` (+ time) — pull DC directory/audit events (4662/5136, `Audit Directory Service Changes`) to **attribute the DNS change to a user** (`itadmin`/`svc-backup`) that this table cannot name.
- **DnsEvents** on `Zone`/`Name` → `Name`/`SubType` — confirm the tampered record is now being **resolved** by clients (the planted `sso`/`autodiscover` actually returning `185.220.101.2`).
- **DeviceLogonEvents / DeviceEvents** on `ServerName` → `DeviceName` (+ time) — tie the change back to the session on **DC01** (the ~09:00–10:00 lateral-movement and process activity that preceded the DNS edits).
- **DeviceNetworkEvents** on `RDATA`/`NewValue` → `RemoteIP` — show hosts subsequently connecting to the planted address `185.220.101.2`/`91.219.236.18`.

## 📚 References
- [DnsAuditEvents — Azure Monitor reference](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/dnsauditevents)
- [DnsEvents — Azure Monitor reference (the sibling query/analytic stream)](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/dnsevents)
- [Gather insights about your DNS infrastructure with the DNS connector (Microsoft Sentinel)](https://learn.microsoft.com/en-us/azure/sentinel/connect-dns-ama)
