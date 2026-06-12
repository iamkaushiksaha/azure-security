# StorageBlobLogs

> **Category:** Azure Resources (Azure Storage — Blob service resource/diagnostic logs)
> **Connector / source:** Azure **Diagnostic settings** on the storage account's **blob** sub-resource (`Microsoft.Storage/storageAccounts/blobServices`), with the `StorageRead` / `StorageWrite` / `StorageDelete` log categories routed to a Log Analytics workspace. Sentinel reads it natively once the workspace is onboarded.
> **Table plan:** Basic-eligible — the reference flags **Basic log = Yes** (also supports ingestion-time DCR and lake-only ingestion). Commonly kept on **Analytics** when analytics-rule / full-KQL support is required for storage detections.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/storagebloblogs

## What this table is
Each row is a single **data-plane request** to the Azure Storage **Blob** service for one storage account — a read, write, list, delete, or metadata operation against a container or blob, captured by the account's diagnostic settings. The operation is in `OperationName` (e.g. `GetBlob`, `PutBlob`, `ListBlobs`, `DeleteBlob`), the object in `Uri` / `ObjectKey` / `AccountName`, the caller in `CallerIpAddress`, and how they authenticated in `AuthenticationType` (`AccountKey`, `SAS`, `OAuth`, `Anonymous`) with the OAuth identity in `RequesterObjectId` / `RequesterUpn` / `RequesterAppId`. Rows appear within a few minutes of the request once `StorageRead`/`StorageWrite`/`StorageDelete` categories are enabled. In a SOC it is the primary table for **data-exfiltration** hunting (high-volume blob egress, mass `ListBlobs`+`GetBlob` enumeration) and **storage misconfiguration / unauthorized-access** hunting (`Anonymous` reads, `AccountKey` use from unexpected IPs after a `listKeys`, SAS abuse).

## Schema
Full column list, validated against the Microsoft Learn reference. (Types are the KQL/Log Analytics types: string, int, long, real, datetime, bool, dynamic, guid.)

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | Coordinated Universal Time (UTC) when the request was received by storage. Primary event time. |
| AccountName | string | The name of the storage account the request targeted. **Not a user** — this is the resource. |
| OperationName | string | The type of REST operation performed (e.g. `GetBlob`, `PutBlob`, `ListBlobs`, `DeleteBlob`, `GetBlobProperties`). The activity key for this table. |
| OperationVersion | string | Storage service version specified when the request was made (the `x-ms-version` header value). |
| OperationCount | int | Number of each logged operation involved in the request, starting at index 0. Most requests are 1; some (e.g. copy) span multiple. |
| Category | string | The category of the requested operation — `StorageRead`, `StorageWrite`, or `StorageDelete`. |
| AuthenticationType | string | How the request was authenticated: `AccountKey`, `SAS`, `OAuth`, or `Anonymous`. Core triage field. |
| AuthenticationHash | string | The hash of the authentication token. |
| AuthorizationDetails | dynamic | Detailed policy information used to authorize the request (RBAC action/role evaluation; JSON). |
| RequesterObjectId | string | The OAuth (Entra) **object ID** of the requester. Populated for `OAuth`; empty for `AccountKey` / `SAS` / `Anonymous`. |
| RequesterUpn | string | The User Principal Name of the requester (OAuth user requests). |
| RequesterAppId | string | The OAuth **application (client) ID** used as the requester. |
| RequesterAudience | string | The OAuth audience of the request. |
| RequesterTenantId | string | The OAuth tenant ID of the identity. |
| RequesterTokenIssuer | string | The OAuth token issuer. |
| CallerIpAddress | string | The IP address of the requester, **including the port number** (e.g. `185.220.101.2:54110`). Strip the port before joining on IP. |
| Uri | string | The Uniform Resource Identifier that was requested (full blob/container URL incl. query string). |
| ObjectKey | string | The key of the requested object, in quotes — `/{account}/{container}/{blob}`. |
| Protocol | string | The protocol used for the operation (e.g. `HTTPS`, `HTTP`). |
| TlsVersion | string | The TLS version used in the connection (e.g. `TLS 1.2`). |
| UserAgentHeader | string | The `User-Agent` header value, in quotes. Distinguishes SDKs/tools (azcopy, Storage Explorer) from generic clients (python-requests, curl). |
| ReferrerHeader | string | The `Referer` header value. |
| ClientRequestId | string | The `x-ms-client-request-id` header value of the request. |
| CorrelationId | string | ID used to correlate logs across resources. Key cross-table / cross-resource join key. |
| StatusCode | string | The HTTP status code for the request, e.g. `200`, `206`, `403`, `404`. **String, not int** — see gotchas. May be `Unknown` if interrupted. |
| StatusText | string | The status of the requested operation (e.g. `Success`, `AuthorizationFailure`, `BlobNotFound`). |
| RequestBodySize | long | Size in bytes of the request packets read by storage. May be empty if the request was unsuccessful. |
| ResponseBodySize | long | Size in bytes of the response packets written by storage. **The egress-volume field for exfil hunting.** May be empty if unsuccessful. |
| RequestHeaderSize | long | Size in bytes of the request header. May be empty if unsuccessful. |
| ResponseHeaderSize | long | Size in bytes of the response header. May be empty if unsuccessful. |
| ContentLengthHeader | long | The `Content-Length` header value of the request sent to the storage service. |
| RequestMd5 | string | Value of the `Content-MD5` / `x-ms-content-md5` header in the request (MD5 of the request content). |
| ResponseMd5 | string | The MD5 hash calculated by the storage service for the response. |
| ServerLatencyMs | real | Time in ms to perform the operation, excluding network latency. |
| DurationMs | real | Total time in ms to perform the operation, including reading the request and sending the response. |
| AccessTier | string | The access tier of the blob/account (Hot/Cool/Cold/Archive). |
| SourceAccessTier | string | The source tier for tier-changing operations. |
| RehydratePriority | string | Priority used to rehydrate an archived blob. |
| ConditionsUsed | string | Semicolon-separated key-value pairs representing the request's conditional headers. |
| Etag | string | The ETag identifier for the returned object, in quotes. |
| LastModifiedTime | datetime | The Last Modified Time (LMT) of the returned object. Empty for operations that can return multiple objects (e.g. `ListBlobs`). |
| ServiceType | string | The service associated with the request (e.g. `blob`). |
| Location | string | The location (region) of the storage account. |
| MetricResponseType | string | Records the metric response, for correlation between metrics and logs. |
| SourceUri | string | The source URI for operations (e.g. server-side copy source). |
| DestinationUri | string | The destination URI for operations (e.g. server-side copy destination). |
| SasExpiryStatus | string | Records SAS-policy violations on the request token (e.g. SAS duration longer than the account SAS policy allows). |
| SchemaVersion | string | The schema version of the log. |
| TenantId | string | The Log Analytics workspace ID. |
| SourceSystem | string | The type of agent that collected the event (`Azure` for Azure Diagnostics). |
| Type | string | The name of the table (`StorageBlobLogs`). |
| _ResourceId | string | Unique resource identifier (ARM ID) of the storage account the record is associated with. |
| _SubscriptionId | string | Unique identifier of the subscription the record is associated with. |
| _BilledSize | real | The record size in bytes. |
| _IsBillable | string | Whether ingesting the data is billable (string `true`/`false`). |

> Full reference table is **60 columns**. Every detection-relevant column (operation, identity/OAuth fields, caller IP, URI/object, status, request/response sizes, correlation IDs, user agent, the `AuthorizationDetails` blob) is listed individually above; the remainder are size/latency, schema/envelope, and billing columns, all of which appear in the table tail.

## Key columns for detection & hunting
- **Identity:** there is no single "user" column. The actor is `AuthenticationType` + (`RequesterObjectId`, `RequesterUpn`, `RequesterAppId`) for **OAuth** requests; for **AccountKey** the only identity is the shared key (and the request blends with any legitimate key user), for **SAS** it's the token, and for **Anonymous** there is no identity at all. `AccountName` is the *target* resource, not the caller.
- **Host / device:** n/a — there is no device/host concept; the closest thing is `CallerIpAddress` + `UserAgentHeader`.
- **Network:** `CallerIpAddress` (the requester IP **with port appended** — split on `:` before joining). `Protocol` / `TlsVersion` for connection posture.
- **Outcome / result:** `StatusCode` (HTTP code, a **string** — `200`/`206`/`403`/`404`/`Unknown`) and `StatusText` (`Success`, `AuthorizationFailure`, `BlobNotFound`, …).
- **Timestamps:** `TimeGenerated` (request received by storage); `LastModifiedTime` (object LMT, single-object ops only).
- **Join keys (to other tables):** `CallerIpAddress` (strip port) ↔ IP columns elsewhere; `RequesterObjectId` ↔ Entra object ID; `RequesterUpn` ↔ `UserPrincipalName`; `RequesterAppId` ↔ app/service-principal ID; `CorrelationId` ↔ Azure `AzureActivity` / `AzureDiagnostics` correlation; `AccountName` / `_ResourceId` ↔ the storage-account resource in `AzureActivity`.

## ⚠️ Schema gotchas
- **`StatusCode` is a STRING, not an int.** Despite holding values like `200`/`403`, the column type is `string` and can also be the literal `Unknown`. Compare as a string (`StatusCode == "200"`) or `toint()` it explicitly; never assume numeric. (`OperationCount` is the int.)
- **`CallerIpAddress` carries the port.** Values look like `185.220.101.2:54110`. Always normalize — `tostring(split(CallerIpAddress, ":")[0])` — before grouping or joining on IP, or every ephemeral port looks like a distinct "IP".
- **Identity is auth-type dependent.** `RequesterObjectId` / `RequesterUpn` / `RequesterAppId` are only populated for `AuthenticationType == "OAuth"`. For `AccountKey`, `SAS`, and `Anonymous` they are **empty** — so a key-based exfil has no user attribution in this table; you must pivot to `AzureActivity` (the `listKeys` that handed out the key) to attribute it.
- **`AccountName` is the storage account, not a person.** New analysts routinely mistake it for the caller. The container/blob path lives in `ObjectKey` / `Uri`.
- **Size fields can be empty on failure.** `ResponseBodySize` / `RequestBodySize` "may be empty" for unsuccessful requests — coalesce (`coalesce(ResponseBodySize, 0L)`) before summing egress, or failed `403`s skew the totals.
- **Category vs operation.** `Category` is only the coarse `StorageRead`/`StorageWrite`/`StorageDelete` bucket; the specific verb is `OperationName`. Filter on `OperationName` for precise hunts.

## 🧪 Sample data
[`StorageBlobLogs_sample.csv`](StorageBlobLogs_sample.csv) — 24 rows. Blob-service diagnostic logs for `stcontosofin` across the morning of 2026-06-10: benign **OAuth** reads/writes from corp egress IPs (`52.170.12.45`, `20.98.111.30`) by `alexw` (Storage Explorer) and the `svc-backup` automation account (azcopy nightly backups), then at **~10:17–10:24** an exfiltration burst from the attacker IP `185.220.101.2` — `ListBlobs` enumeration of the `finance` container followed by large-`ResponseBodySize` `GetBlob` pulls (a 512 MB GL export, a 256 MB bank-statement archive, a 73 MB customer-master CSV) using **AccountKey** (the key freshly listed via `listKeys` in `AzureActivity`), plus **Anonymous** reads of a misconfigured `public-finance` container, a failed `SAS` `403`, and a `DeleteBlob` of the access-log to cover tracks. This is the **blob-exfiltration slice (~10:20) of "Operation Quiet Ledger"** — it follows the Azure storage-key list and precedes the Key Vault / NSG actions.

The sample uses this curated subset of **real** columns: `TimeGenerated`, `AccountName`, `OperationName`, `AuthenticationType`, `CallerIpAddress`, `RequesterObjectId`, `RequesterUpn`, `RequesterAppId`, `Uri`, `ObjectKey`, `StatusCode`, `StatusText`, `ResponseBodySize`, `RequestBodySize`, `UserAgentHeader`, `Category`, `Protocol`, `TlsVersion`, `CorrelationId`.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · High-volume blob egress by caller IP — [T1567](https://attack.mitre.org/techniques/T1567/)
**Hypothesis:** An external IP that pulls an unusually large total volume of blob data in a short window — far above any legitimate reader — is exfiltrating from storage.
```kusto
StorageBlobLogs
| where OperationName == "GetBlob" and StatusCode in ("200", "206")
| extend CallerIp = tostring(split(CallerIpAddress, ":")[0])
| summarize TotalBytes = sum(coalesce(ResponseBodySize, 0L)),
            Blobs = dcount(ObjectKey), Ops = count(),
            AuthTypes = make_set(AuthenticationType),
            FirstSeen = min(TimeGenerated), LastSeen = max(TimeGenerated)
    by CallerIp, AccountName
| extend TotalMB = round(TotalBytes / 1048576.0, 1)
| where TotalMB > 100
| sort by TotalBytes desc
```
**Triage:** True positive = `185.220.101.2` pulling hundreds of MB from `stcontosofin` over a few minutes via `AccountKey`, no corresponding business reason. Benign = `svc-backup` / azcopy reads of the `backups` container, or a known analyst IP doing OAuth reports.

### H2 · Anonymous (public) blob access — [T1530](https://attack.mitre.org/techniques/T1530/)
**Hypothesis:** Any `AuthenticationType == "Anonymous"` request indicates a publicly-exposed container; an external IP reading/enumerating finance data anonymously is unauthorized access to a misconfigured store.
```kusto
StorageBlobLogs
| where AuthenticationType == "Anonymous"
| extend CallerIp = tostring(split(CallerIpAddress, ":")[0])
| project TimeGenerated, CallerIp, AccountName, OperationName, ObjectKey,
          StatusCode, ResponseBodySize, UserAgentHeader
| sort by TimeGenerated asc
```
**Triage:** True positive = anonymous `GetBlob` / `ListBlobs` against a finance/`public-finance` container from an external IP (`185.220.101.2`), confirming public exposure. Benign = anonymous reads of intentionally-public static content (logos, public docs) from a CDN/edge — validate the container's intended access level.

### H3 · AccountKey or SAS access from a new / non-corporate IP — [T1078.004](https://attack.mitre.org/techniques/T1078.004/)
**Hypothesis:** Shared-key or SAS access (no per-user identity) from an IP that never legitimately touches this account — especially right after a `listKeys` — is stolen-credential use.
```kusto
StorageBlobLogs
| where AuthenticationType in ("AccountKey", "SAS")
| extend CallerIp = tostring(split(CallerIpAddress, ":")[0])
| where CallerIp !in ("52.170.12.45", "20.98.111.30")   // known corp egress
| summarize Ops = count(), Operations = make_set(OperationName),
            Containers = make_set(tostring(split(ObjectKey, "/")[2])),
            Bytes = sum(coalesce(ResponseBodySize, 0L)),
            FirstSeen = min(TimeGenerated), LastSeen = max(TimeGenerated)
    by CallerIp, AccountName, AuthenticationType
| sort by Bytes desc
```
**Triage:** True positive = `AccountKey`/`SAS` from `185.220.101.2` hitting the `finance` container minutes after the AzureActivity `listKeys`. Benign = a backup runner or partner integration on a documented IP — confirm the IP allow-list.

### H4 · Failure spike or anti-forensic delete during a burst — [T1485](https://attack.mitre.org/techniques/T1485/)
**Hypothesis:** A cluster of `DeleteBlob` and authorization failures from the same caller during an access burst suggests cleanup of audit trails or probing of access.
```kusto
StorageBlobLogs
| where OperationName == "DeleteBlob" or StatusCode == "403" or StatusText == "AuthorizationFailure"
| extend CallerIp = tostring(split(CallerIpAddress, ":")[0])
| project TimeGenerated, CallerIp, AccountName, OperationName, ObjectKey,
          AuthenticationType, StatusCode, StatusText
| sort by TimeGenerated asc
```
**Triage:** True positive = the attacker IP deleting an `.audit/access-log.json` and racking up `403`s on SAS-protected blobs mid-exfil. Benign = a lifecycle/cleanup job deleting expired blobs under the backup identity.

## 🔗 Correlates with
- **AzureActivity** on `CorrelationId`, and on `_ResourceId` / `AccountName` (the storage account) — pivot from the blob burst back to the `Microsoft.Storage/storageAccounts/listKeys/action` that handed the attacker the account key just before 10:20, and to the role assignment that enabled it.
- **SigninLogs** on `RequesterObjectId` ↔ `UserId` / `RequesterUpn` ↔ `UserPrincipalName` — for OAuth requests, tie the storage access to the risky Entra sign-in (e.g. alexw from the Netherlands); note that the AccountKey exfil has **no** identity here, which is itself the tell.
- **AzureNetworkAnalytics / NSG flow logs** on `CallerIpAddress` (port-stripped) — corroborate the egress connection from `185.220.101.2` and downstream Key Vault / NSG activity (~10:40).
- **DeviceNetworkEvents** on `CallerIpAddress` ↔ `RemoteIP` — link the attacker IP seen at storage to the same IP observed beaconing from FIN-WS-07.

## 📚 References
- StorageBlobLogs table reference — https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/storagebloblogs
- Monitor Azure Blob Storage — https://learn.microsoft.com/en-us/azure/storage/blobs/monitor-blob-storage
- Azure Storage analytics logs (field reference) — https://learn.microsoft.com/en-us/azure/storage/common/storage-analytics-logging
