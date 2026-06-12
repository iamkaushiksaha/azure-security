# AKSAuditAdmin

> **Category:** Containers (Azure Kubernetes Service — Kubernetes API Server audit, *admin* subset) / Audit, Azure Resources. Solution: `LogManagement`.
> **Connector / source:** **AKS Diagnostic Settings** with the **`kube-audit-admin`** log category routed to a **Resource-specific** destination (so it lands in this dedicated table rather than `AzureDiagnostics`). Emitted by the managed control plane's **kube-apiserver** audit backend. No agent runs on the nodes for this — it is control-plane diagnostic data.
> **Table plan:** **Basic log supported** — the reference flags **Basic log: Yes** (also ingestion-time DCR support and lake-only ingestion). Defaults to Analytics unless the workspace explicitly sets the table to Basic/Auxiliary.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/aksauditadmin

## What this table is
Each row is a **single Kubernetes API Server audit event** for an Azure Kubernetes Service cluster — one client request to the API (and the stage it reached), capturing **who** called (`User`), **from where** (`SourceIps`), **what verb** (`Verb`: create/update/patch/delete/…), **against which object** (`ObjectRef`, `RequestUri`), and **the outcome** (`ResponseStatus.code`). It is emitted by the managed control plane whenever Diagnostic Settings route the `kube-audit-admin` category to a resource-specific table. Crucially, **`AKSAuditAdmin` is the filtered "admin" stream: it deliberately excludes the high-volume `get`/`list`/`watch` read events**, leaving only **mutating and privileged operations** — so it is the low-noise table you reach for first to detect **RBAC tampering, privileged/hostPath pod creation, `pods/exec` into running containers, secret/token creation, and deletion of logging or policy objects**. Its sibling **`AKSAudit`** carries the *complete* stream (reads included) and is far noisier/costlier.

### `AKSAudit` vs `AKSAuditAdmin` — which to use
Both tables share the **exact same schema** (identical 24 columns); they differ only in **which events are written**:

| | `AKSAuditAdmin` (this table) | `AKSAudit` |
|---|---|---|
| Diagnostic category | `kube-audit-admin` | `kube-audit` |
| Events included | **Excludes** `get` / `list` / `watch` — i.e. **mutating + privileged only** (create, update, patch, delete, `exec`, `attach`, `portforward`, token requests, RBAC writes) | **All** API events, including read verbs |
| Volume / cost | Low — write-side only | High — dominated by read traffic |
| Best for | **Write-side detections**: RBAC abuse, privilege escalation, persistence, defense evasion, suspicious workload creation | Reconnaissance / read-access hunting (who *listed* secrets, enumerated the cluster), full forensic timeline |

**Rule of thumb:** build standing analytics on **`AKSAuditAdmin`** (cheaper, mutation-focused, fewer false positives); pivot to **`AKSAudit`** when you need to see the reconnaissance that preceded a change (e.g. the `list secrets` that came before a `create` of an exfil token), or for complete incident reconstruction. **Do not enable both categories to the same workspace expecting deduplication — admin events appear in *both* `kube-audit` and `kube-audit-admin`, so dual-routing double-bills.**

## Schema
Full column list, validated against the Microsoft Learn reference. Types are KQL/Log Analytics types. This is the complete 24-column schema (identical to `AKSAudit`); the heavy detection value lives in the **dynamic** blobs (`User`, `SourceIps`, `ObjectRef`, `ResponseStatus`, `RequestObject`, `ResponseObject`, `Annotations`).

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | Event generation time (UTC). |
| Verb | string | The Kubernetes verb for the request (`create`, `update`, `patch`, `delete`, `deletecollection`, …). For **non-resource** requests it is the lower-cased HTTP method. **Never `get`/`list`/`watch` in this table** (those are filtered out). |
| RequestUri | string | The full request URI, e.g. `/apis/rbac.authorization.k8s.io/v1/clusterrolebindings/...`. Subresources (`/exec`, `/token`, `/portforward`, `/attach`) and query strings (`?command=...`) appear here. |
| User | dynamic | Authenticated caller metadata: `username` (UPN, `system:serviceaccount:<ns>:<sa>`, or `system:...`), optional `uid`, and `groups[]`. **The primary identity field — nested, not a flat column.** |
| SourceIps | dynamic | JSON **array** of source IPs (originating client + intermediate proxies). Index `[0]` is normally the client. |
| ObjectRef | dynamic | The Kubernetes object the request targeted: `resource`, `namespace`, `name`, `subresource`, `apiGroup`, `apiVersion`. (Absent for non-resource requests.) |
| ResponseStatus | dynamic | Response status incl. the HTTP `code` (200/201/101/403/…); on failure also `status:"Failure"`, `reason`, and `message`. **`code` is a number *inside* the dynamic blob, not a top-level int column.** |
| Stage | string | Request-handling stage at which this event fired: `RequestReceived`, `ResponseStarted`, `ResponseComplete`, `Panic`. Long-lived streams (`exec`) emit `ResponseStarted` (HTTP `101` upgrade). |
| Level | string | Audit verbosity recorded: `Metadata`, `Request`, or `RequestResponse` (the latter includes request/response bodies). |
| AuditId | string | Unique audit ID generated per request. The **same `AuditId` appears across the multiple stage rows** of one request — use it to collapse/correlate stages. |
| RequestReceivedTime | datetime | Time the API Server first received the request. |
| StageReceivedTime | datetime | Time the request reached the current audit stage. |
| RequestObject | dynamic | The submitted Kubernetes object (full body) **or** the literal string `"skipped-too-big-size-object"`. Only present at `Level == "RequestResponse"` (or `Request`). Omitted for non-resource requests. |
| ResponseObject | dynamic | The returned Kubernetes object, or `"skipped-too-big-size-object"`. Present only at `RequestResponse`. Omitted for non-resource requests. |
| Annotations | dynamic | Unstructured key-value map set by admission plugins along the serving chain (e.g. `authorization.k8s.io/decision`, `pod-security.kubernetes.io/enforce-policy`). Included at the Metadata level. |
| UserAgent | string | Client user-agent string (e.g. `kubectl/v1.30.0 (linux/amd64)`, `curl/8.5.0`, controller names). Useful for spotting non-`kubectl` tooling. |
| PodName | string | Name of the API-server pod emitting the audit event (control-plane component, **not** the targeted workload — the target is in `ObjectRef.name`). |
| SourceSystem | string | Agent type that collected the event (typically `Azure` for this diagnostic source). |
| _ResourceId | string | ARM resource ID of the AKS managed cluster the record belongs to. |
| _SubscriptionId | string | Subscription ID the record is associated with. |
| TenantId | string | The Log Analytics workspace ID. |
| Type | string | The table name (`AKSAuditAdmin`). |
| _BilledSize | real | Record size in bytes. |
| _IsBillable | string | Whether ingestion is billable (string `"true"`/`"false"`). |

**Total: 24 columns** (no column invented; same set as `AKSAudit`).

## Key columns for detection & hunting
- **Identity (actor):** `User` (dynamic). Use `tostring(User.username)` — values are a human UPN (`alexw@contoso.com`), a service account (`system:serviceaccount:<namespace>:<name>`), or a built-in (`system:anonymous`, `system:masters` member). Groups via `User.groups`; a request running as **`system:masters`** is effectively unrestricted cluster-admin.
- **Host / device:** No node/VM column. The **subject** of the action is the targeted object — `tostring(ObjectRef.namespace)` + `tostring(ObjectRef.name)` + `tostring(ObjectRef.resource)`. `PodName` is the **API-server** pod, not the workload. Cluster identity is in `_ResourceId` (e.g. `aks-prod-01`).
- **Network:** `SourceIps` (dynamic **array**) — `tostring(SourceIps[0])` is the calling client IP. External/non-pod IPs (not `10.244.0.0/16` pod CIDR, not corporate egress) calling mutating verbs are a strong signal.
- **Outcome / result:** `ResponseStatus.code` — `toint(ResponseStatus.code)`. `200`/`201` = success, `101` = protocol upgrade (exec/attach/portforward streams), `403` = Forbidden (RBAC/PodSecurity denial — **failed attempts are still recorded and are themselves a signal**), `401` = unauthenticated. Failure detail in `ResponseStatus.message`/`reason`.
- **Timestamps:** `TimeGenerated` (event time); `RequestReceivedTime` (API receipt); `StageReceivedTime` (per-stage).
- **Join keys (to other tables):** `tostring(User.username)` (UPN) → `AADUserId`/UPN in `SigninLogs`, `AuditLogs`, `OfficeActivity`; `tostring(SourceIps[0])` → `IPAddress`/`RemoteIP` across sign-in, network, and DNS tables; `_ResourceId`/`_SubscriptionId` → `AzureActivity` (cluster-level control-plane ops); `AuditId` → collapses the multi-stage rows of a single request within this table.

## ⚠️ Schema gotchas
- **`get`/`list`/`watch` are NOT here — by design.** This is the `kube-audit-admin` (mutating) subset. A query that filters `Verb in ("get","list")` returns nothing. For read/recon hunting (who *listed* secrets, enumerated RBAC), query **`AKSAudit`** instead. State this in any cross-table playbook so analysts don't conclude "no reconnaissance happened" from this table alone.
- **The whole identity is in a dynamic blob.** There is **no flat `Account`/`UserPrincipalName` column** — always `tostring(User.username)`. Service accounts and humans share that field; distinguish them by the `system:serviceaccount:` prefix. Group membership (incl. `system:masters`) is in the `User.groups` array.
- **`ResponseStatus.code` is a number *inside* a dynamic field, not a typed int column.** Use `toint(ResponseStatus.code)`; never compare a top-level `ResponseStatus` to an integer. Likewise `SourceIps` is a JSON **array** — index it (`SourceIps[0]`) or `mv-expand`; don't string-compare the whole array.
- **One request → multiple rows.** A single API call can emit a `ResponseStarted` row and a `ResponseComplete` row (and more) that **share the same `AuditId`**. `exec`/`attach`/`portforward` typically surface as `ResponseStarted` with HTTP **`101`** and may never reach `ResponseComplete`. Dedupe/`summarize arg_max(...) by AuditId` when counting distinct operations.
- **Bodies depend on `Level`.** `RequestObject`/`ResponseObject` are only populated at `Level == "RequestResponse"` (or `Request`); at `Metadata` level they are empty, and large bodies are replaced by the literal string `"skipped-too-big-size-object"`. Don't assume the manifest is always available.
- **`subresource` lives in `ObjectRef` *and* the URI.** Privileged actions like `pods/exec`, `serviceaccounts/<name>/token`, `pods/portforward` show up as `ObjectRef.subresource` and as a path segment in `RequestUri`. The base `resource` is just `pods`/`serviceaccounts`, so filter on the **subresource**, not the resource, to catch them.
- **Resource-specific destination is mandatory.** If Diagnostic Settings use the legacy **Azure diagnostics** mode, rows land in `AzureDiagnostics` (columns flattened/prefixed) and **this table stays empty**. Confirm the destination is *Resource-specific*.

## 🧪 Sample data
[`AKSAuditAdmin_sample.csv`](AKSAuditAdmin_sample.csv) — 20 rows. The rows tell the **Operation Quiet Ledger** AKS step (~11:00–11:35 on cluster **`aks-prod-01`**): amid legitimate deployments by **dvora** (deploy `ledger-api`/`web-portal`, a rolebinding) and benign controller/service-account writes, a **compromised `alexw@contoso.com`** identity calling from the attacker IP **`185.220.101.2`** runs the write-side kill chain — `create pods/exec` into `coredns`, an attempt to **create a privileged pod (blocked `403` by PodSecurity)**, then a successful debug pod, **`patch` the `cluster-admin-binding` clusterrolebinding** and create a new one (privilege escalation), **create a serviceaccount `token`** (persistence), **`delete` the `ama-logs` DaemonSet and `azure-monitor-settings` ConfigMap** (defense evasion — killing the log pipeline), create an `exfil-token` secret, and exec to read a SA token — before **itadmin** deletes the rogue binding in remediation.
The sample uses this curated subset of **real** columns: `TimeGenerated`, `Verb`, `RequestUri`, `User`, `SourceIps`, `ObjectRef`, `ResponseStatus`, `Stage`, `Level`, `AuditId`, `UserAgent`, `PodName`. This is the **AKS exec / RBAC-tamper / secret-read step (~11:00)** of the cross-table attack scenario, following the Key Vault / NSG actions (~10:40).

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · `pods/exec` into a running container — [T1609](https://attack.mitre.org/techniques/T1609/)
**Hypothesis:** An interactive `exec`/`attach` into a pod (especially a control-plane / `kube-system` pod, from a non-pod source IP) is a hands-on-keyboard breakout into the cluster runtime.
```kusto
AKSAuditAdmin
| where Verb == "create"
| where RequestUri has "/exec" or RequestUri has "/attach" or tostring(ObjectRef.subresource) in ("exec","attach")
| extend actor = tostring(User.username), srcip = tostring(SourceIps[0])
| extend ns = tostring(ObjectRef.namespace), pod = tostring(ObjectRef.name)
| project TimeGenerated, actor, srcip, ns, pod, RequestUri, UserAgent, code = toint(ResponseStatus.code)
| sort by TimeGenerated asc
```
**Triage:** True positive = a human/`cluster-readers` identity exec-ing into `kube-system` pods (`coredns`, `konnectivity-agent`) from `185.220.101.2`. Benign = an SRE debugging their own app pod from corporate egress during an incident.

### H2 · ClusterRoleBinding created/modified — privilege escalation — [T1098](https://attack.mitre.org/techniques/T1098/)
**Hypothesis:** Creating or patching `clusterrolebindings`/`rolebindings` to grant `cluster-admin` (or bind to `system:masters`) is the canonical Kubernetes privilege-escalation / account-manipulation move.
```kusto
AKSAuditAdmin
| where Verb in ("create","update","patch")
| where tostring(ObjectRef.resource) in ("clusterrolebindings","rolebindings","clusterroles","roles")
| extend actor = tostring(User.username), srcip = tostring(SourceIps[0])
| project TimeGenerated, actor, srcip, Verb, binding = tostring(ObjectRef.name), RequestUri, code = toint(ResponseStatus.code)
| sort by TimeGenerated asc
```
**Triage:** True positive = a low-privilege identity (`alexw`, `cluster-readers`) patching `cluster-admin-binding` or creating `ops-support-crb` from the attacker IP. Benign = the platform team (`itadmin`/`dvora`) provisioning a namespace rolebinding via change management. *(`itadmin`'s later `delete` of `ops-support-crb` is remediation, not attack.)*

### H3 · Deletion of logging / monitoring / policy objects — defense evasion — [T1562.001](https://attack.mitre.org/techniques/T1562/001/)
**Hypothesis:** Deleting the Azure Monitor agent DaemonSet, its settings ConfigMap, or admission/policy objects blinds detection before the next stage.
```kusto
AKSAuditAdmin
| where Verb in ("delete","deletecollection")
| where tostring(ObjectRef.name) has_any ("ama-logs","azure-monitor","omsagent","falco","gatekeeper","audit","kyverno")
   or tostring(ObjectRef.resource) in ("validatingwebhookconfigurations","mutatingwebhookconfigurations")
| extend actor = tostring(User.username), srcip = tostring(SourceIps[0])
| project TimeGenerated, actor, srcip, Verb, ns = tostring(ObjectRef.namespace), target = tostring(ObjectRef.name), RequestUri
| sort by TimeGenerated asc
```
**Triage:** True positive = `alexw` from `185.220.101.2` deleting `ama-logs`/`azure-monitor-settings`. Benign = a documented monitoring-stack upgrade/redeploy by the platform SA in a maintenance window.

### H4 · ServiceAccount token minted or secret created for exfil/persistence — [T1528](https://attack.mitre.org/techniques/T1528/)
**Hypothesis:** A `serviceaccounts/token` request or fresh `secret` create — especially against a high-privilege controller SA, from an interactive client — provisions a long-lived credential for persistence or token theft.
```kusto
AKSAuditAdmin
| where Verb == "create"
| where tostring(ObjectRef.subresource) == "token" or RequestUri has "/token"
   or (tostring(ObjectRef.resource) == "secrets")
| extend actor = tostring(User.username), srcip = tostring(SourceIps[0])
| project TimeGenerated, actor, srcip, ns = tostring(ObjectRef.namespace), target = tostring(ObjectRef.name), RequestUri, UserAgent
| sort by TimeGenerated asc
```
**Triage:** True positive = `curl`-agent token mint against `clusterrole-aggregation-controller` and an `exfil-token` secret create by `alexw`. Benign = a CI/CD or operator SA (`prometheus-operator`, `helm`) creating expected secrets/tokens in its own namespace.

## 🔗 Correlates with
- **AKSAudit** on `AuditId` / `User.username` — pivot to the **full** stream to see the `get`/`list`/`watch` **reconnaissance** (e.g. `list secrets`, RBAC enumeration) that this admin-only table filters out, and to reconstruct the complete request timeline.
- **SigninLogs / AuditLogs** on `tostring(User.username)` → UPN — tie the cluster identity `alexw@contoso.com` back to the **risky Entra sign-in** (NL, `185.220.101.2`) and any directory role/group changes from earlier in the incident.
- **AzureActivity** on `_ResourceId` / `_SubscriptionId` → AKS managed-cluster resource — correlate **control-plane / ARM** operations on `aks-prod-01` (run-command, credential listing, node-pool changes) with in-cluster API abuse.
- **DeviceNetworkEvents / DnsEvents** on `tostring(SourceIps[0])` → `RemoteIP` / resolved IP — show the same attacker IP `185.220.101.2` (and `91.219.236.18`) appearing across host, network, and DNS telemetry for the broader campaign.

## 📚 References
- [AKSAuditAdmin — Azure Monitor reference](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/aksauditadmin)
- [AKSAudit — Azure Monitor reference (the full, unfiltered sibling stream)](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/aksaudit)
- [Monitor Azure Kubernetes Service (AKS) — control-plane / resource logs & diagnostic categories](https://learn.microsoft.com/en-us/azure/aks/monitor-aks)
- [Kubernetes Auditing — audit levels, stages, and event structure](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)
