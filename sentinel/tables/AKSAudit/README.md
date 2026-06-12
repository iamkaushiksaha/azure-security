# AKSAudit

> **Category:** Containers / Audit (Azure Kubernetes Service — Kubernetes API server audit log)
> **Connector / source:** AKS managed-cluster **Diagnostic Settings** with the **`kube-audit`** log category routed to a Log Analytics workspace in **Resource-specific** destination mode (this fills `AKSAudit`/`AKSAuditAdmin`; legacy Azure-diagnostics mode lands in `AzureDiagnostics` instead). Emitted by the Kubernetes API server's audit backend on the AKS control plane.
> **Table plan:** Basic supported — the reference flags **Basic log: Yes** (also ingestion-time DCR support and lake-only ingestion). Defaults to Analytics unless the workspace sets the table to Basic.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/aksaudit

## What this table is
Each row is a **single Kubernetes API server audit event** from an AKS cluster: one authenticated (or anonymous) call to the API server — who called it, from where, what verb, against which object, and the response code. `AKSAudit` is the **full** audit stream and explicitly **includes the high-volume `get` and `list` (read) verbs**; its sibling `AKSAuditAdmin` carries only the mutating subset (`create`/`update`/`patch`/`delete`), so use `AKSAuditAdmin` when you only care about changes and `AKSAudit` when you need reads too (secret enumeration, recon, `pods/exec`). Rows appear only when **Diagnostic Settings** route the `kube-audit` category to the workspace in resource-specific mode. In a SOC it is the primary source for **detecting attacker activity inside a cluster** — service-account/identity abuse, secret theft, `pods/exec` into running workloads (a remote-shell into a container), privileged-pod and RBAC manipulation, and reconnaissance against the API.

## Schema
Full column list, validated against the Microsoft Learn reference. Types are KQL/Log Analytics types. Much of the security-relevant content lives in **dynamic** columns (`User`, `SourceIps`, `ObjectRef`, `ResponseStatus`, `RequestObject`, `ResponseObject`, `Annotations`) and must be unpacked with `tostring()` / `toint()` / `parse_json`.

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | Event generation time (UTC). |
| AuditId | string | Unique audit ID generated for each request. The stable key for an individual API call across its stages. |
| Stage | string | Request-handling stage at which this event was generated: `RequestReceived`, `ResponseStarted`, `ResponseComplete`, `Panic`. |
| StageReceivedTime | datetime | Time when the request reached the current audit stage. |
| RequestReceivedTime | datetime | Time when the API server first received the request. |
| Level | string | Audit level of the event: `Metadata`, `Request`, `RequestResponse`. Controls whether request/response bodies are captured. |
| Verb | string | The Kubernetes verb for the request (`get`, `list`, `watch`, `create`, `update`, `patch`, `delete`, `deletecollection`); for non-resource requests this is the lower-cased HTTP method. |
| RequestUri | string | The URI of the request the client made to the server (path + query string — carries namespace, resource, name, and subresources such as `exec`). |
| User | dynamic | Authenticated user metadata of the requesting client: `username`, optional `uid`, `groups[]`, and an `extra` bag (on AKS+Entra integration the Entra object id appears under `extra.oid`). |
| ObjectRef | dynamic | The Kubernetes object reference this event targeted: `resource`, `namespace`, `name`, `subresource`, `apiGroup`, `apiVersion`. Does not apply to `list` or non-resource requests. |
| ResponseStatus | dynamic | Response status including the HTTP `code`; in error cases also `status`, `reason`, and `message`. |
| SourceIps | dynamic | Array of source IP addresses for the originating client and any intermediate proxies. |
| UserAgent | string | The user-agent string presented by the originating client (e.g. `kubectl/...`, `kubelet/...`, controller user-agents). |
| Annotations | dynamic | Unstructured key-value map set by admission/authorization plugins in the serving chain (e.g. `authorization.k8s.io/decision`, `...reason`). Present at the Metadata level. |
| RequestObject | dynamic | Kubernetes API object from the **request** body (object form) or the string `"skipped-too-big-size-object"`. Omitted for non-resource requests and when `Level` < `Request`. |
| ResponseObject | dynamic | Kubernetes API object from the **response** body, or `"skipped-too-big-size-object"`. Omitted for non-resource requests and when `Level` < `RequestResponse`. |
| PodName | string | Name of the (control-plane) pod emitting this audit event. Frequently empty for user `kubectl` calls. |
| SourceSystem | string | Type of agent the event was collected by (`Azure` for Azure Diagnostics, etc.). |
| TenantId | string | The Log Analytics workspace ID. |
| Type | string | The name of the table (`AKSAudit`). |
| _ResourceId | string | ARM resource id of the AKS managed cluster the record is associated with. |
| _SubscriptionId | string | Unique identifier for the subscription the record is associated with. |
| _BilledSize | real | The record size in bytes. |
| _IsBillable | string | Whether ingesting the data is billable (string `true`/`false`); `false` is not billed. |

> Every column from the reference is listed (the page exposes ~22 distinct columns plus the `_`-prefixed billing/identity columns). No column has been invented. The detection-critical **dynamic** blobs are `User`, `SourceIps`, `ObjectRef`, `ResponseStatus`, `RequestObject`, `ResponseObject`, and `Annotations` (note `Verb` is a flat **string**, not dynamic).

## Key columns for detection & hunting
- **Identity (actor):** `tostring(User.username)` — for an Entra-integrated AKS user this is the UPN (e.g. `alexw@contoso.com`); for in-cluster identities it is a service-account principal (`system:serviceaccount:<ns>:<name>`), a node (`system:node:<vmss>`), or a system principal (`system:apiserver`, `system:kube-scheduler`). Groups: `User.groups` (array); Entra object id: `tostring(User.extra.oid[0])`.
- **Host / device:** there is **no `Computer`/`DeviceName` column**. The cluster is `_ResourceId` (`.../managedclusters/aks-prod-01`); `PodName` names the *control-plane* pod for system events; the *target* workload is `tostring(ObjectRef.name)` in `tostring(ObjectRef.namespace)`.
- **Network:** `SourceIps` is a **dynamic array** — the client IP is `tostring(SourceIps[0])` (e.g. `185.220.101.2`). There is no destination/port column.
- **Outcome / result:** `toint(ResponseStatus.code)` — an HTTP status (200 OK, 201 Created, **101** Switching Protocols for a successful `exec`/`attach`/`portforward` upgrade, 403 Forbidden, 404). On failure, `tostring(ResponseStatus.reason)` / `tostring(ResponseStatus.message)` carry the RBAC denial text. **It is a number inside a dynamic blob, not a top-level int.**
- **Timestamps:** `TimeGenerated` (event time); `RequestReceivedTime` (when the API server first saw the request); `StageReceivedTime` (per-stage).
- **Join keys (to other tables):** `tostring(User.username)` / `tostring(User.extra.oid[0])` → `UserPrincipalName` / Entra object id in `SigninLogs`, `AADNonInteractiveUserSignInLogs`, `AuditLogs`; `tostring(SourceIps[0])` → `IPAddress` / `RemoteIP` in sign-in and network tables; `_ResourceId` / `_SubscriptionId` → `AzureActivity` (cluster-level ARM ops, `listClusterUserCredential`); `AuditId` to correlate the same call across stages and with `AKSAuditAdmin`.

## ⚠️ Schema gotchas
- **Almost everything is in dynamic JSON — `tostring()`/`toint()` before you filter.** `User`, `ObjectRef`, `ResponseStatus`, and `SourceIps` are dynamic (`Verb` and `RequestUri` are flat strings). Use `tostring(User.username)`, `tostring(ObjectRef.resource)`, `toint(ResponseStatus.code)`, `tostring(SourceIps[0])`. Filtering on a dynamic column without a cast silently misbehaves.
- **`ResponseStatus.code` is a number nested in a blob, not a top-level int** — there is no flat `ResultType`. Compare `toint(ResponseStatus.code) == 403`, never a bare top-level field. A successful `exec`/`attach`/`portforward` returns **101 (Switching Protocols)**, not 200 — don't filter exec on `code == 200`.
- **`AKSAudit` vs `AKSAuditAdmin`.** `AKSAudit` includes reads (`get`/`list`/`watch`); `AKSAuditAdmin` is mutations only. Secret **enumeration** and `pods/exec` recon are visible **only in `AKSAudit`** — a detection written against `AKSAuditAdmin` will miss them.
- **`pods/exec` is encoded two ways — check both.** `tostring(ObjectRef.subresource) == "exec"` is the reliable signal; the command also appears URL-encoded in `RequestUri` (`/pods/<name>/exec?command=...`). The same applies to `attach`, `portforward`, and `proxy`.
- **No `Computer`/`DeviceName`; the namespace lives in two places.** Host joins must use `_ResourceId` (the cluster), not `Computer`. The namespace is `tostring(ObjectRef.namespace)` for resource calls but only inside `RequestUri` for `list` (where `ObjectRef` may be absent).
- **Volume + plan caveat.** `AKSAudit` is high-cardinality because it carries every read; the reference flags **Basic log: Yes**. Under Basic/Auxiliary, scheduled-analytics rules and cross-table `join` are restricted — confirm the table's plan before building alerting, and expect heavy `get`/`list` controller/kubelet noise to filter out.

## 🧪 Sample data
[`AKSAudit_sample.csv`](AKSAudit_sample.csv) — 22 rows. The rows tell the **container-attack step (~11:00 on cluster `aks-prod-01`)** of Operation Quiet Ledger: amid benign control-plane noise (cluster-autoscaler, kube-controller-manager `list pods`, kubelet/`system:node` reads, scheduler lease renewals, an `system:apiserver` health check, and a benign `meganb` `get configmap` in `hr`), the **compromised `alexw@contoso.com`** connecting from **`185.220.101.2`** enumerates and reads secrets in namespace **`finance`** (`list secrets`, `get finance-db-credentials`, `get` a service-account token secret), execs into two running pods (**`pods/exec` → code 101**, one running `/bin/sh`, one `cat`-ing the in-pod `serviceaccount/token`), **creates a `pause-debug` pod**, **mints a `serviceaccounts/default/token`**, and trips a **403 Forbidden** trying to `list secrets` at cluster scope.
The sample uses this curated subset of **real** columns: `TimeGenerated`, `AuditId`, `Stage`, `Level`, `Verb`, `RequestUri`, `User`, `SourceIps`, `ObjectRef`, `ResponseStatus`, `UserAgent`, `PodName`, `SourceSystem`, `_ResourceId`. This is the **AKS exec / secret-read step (~11:00 on `aks-prod-01`)**, the final on-keyboard stage after the Key Vault / NSG actions (~10:40).

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · Interactive shell into a running container (`pods/exec`) — [T1609](https://attack.mitre.org/techniques/T1609/)
**Hypothesis:** A `create` against the `pods/exec` subresource is a remote shell into a live workload — rarely legitimate from a human kubectl in production, and a hallmark of container compromise (also covers `attach`/`portforward`).
```kusto
AKSAudit
| where Verb == "create"
| where tostring(ObjectRef.subresource) in ("exec", "attach", "portforward") or RequestUri has "/exec?"
| extend actor = tostring(User.username), srcIp = tostring(SourceIps[0]),
         ns = tostring(ObjectRef.namespace), pod = tostring(ObjectRef.name),
         code = toint(ResponseStatus.code)
| where actor !startswith "system:"
| project TimeGenerated, actor, srcIp, ns, pod, sub = tostring(ObjectRef.subresource), code, RequestUri
| sort by TimeGenerated asc
```
**Triage:** True positive = `alexw@contoso.com` from `185.220.101.2` exec-ing `finance` pods with `code == 101`. Benign = a known operator/CI principal debugging in a non-prod namespace within a change window.

### H2 · Secret enumeration & service-account token theft — [T1552.007](https://attack.mitre.org/techniques/T1552/007/)
**Hypothesis:** A non-system principal that **lists** secrets and then **gets** individual secrets / mints service-account tokens is harvesting credentials from the cluster.
```kusto
AKSAudit
| extend actor = tostring(User.username), res = tostring(ObjectRef.resource),
         sub = tostring(ObjectRef.subresource), v = Verb,
         ns = tostring(ObjectRef.namespace), code = toint(ResponseStatus.code)
| where actor !startswith "system:"
| where (res == "secrets" and v in ("list","get"))
     or (res == "serviceaccounts" and sub == "token" and v == "create")
| summarize events = count(), verbs = make_set(strcat(v,":",res,iff(sub=="","",strcat("/",sub)))),
            namespaces = make_set(ns), firstSeen = min(TimeGenerated), lastSeen = max(TimeGenerated)
            by actor, srcIp = tostring(SourceIps[0])
| where events >= 2
| sort by events desc
```
**Triage:** True positive = one identity touching `list secrets` + multiple `get secrets` + `serviceaccounts/.../token create` in minutes. Benign = a controller service account (excluded by `!startswith "system:"`) or a one-off operator read.

### H3 · API authorization failures — RBAC probing / privilege boundaries — [T1613](https://attack.mitre.org/techniques/T1613/)
**Hypothesis:** A burst of `403 Forbidden` responses for one principal indicates it is probing what it can reach (e.g. attempting cluster-scope `list secrets` after namespace-scoped access).
```kusto
AKSAudit
| where toint(ResponseStatus.code) == 403
| extend actor = tostring(User.username), srcIp = tostring(SourceIps[0]),
         res = tostring(ObjectRef.resource), reason = tostring(ResponseStatus.reason)
| where actor !startswith "system:"
| project TimeGenerated, actor, srcIp, Verb, res, reason,
          message = tostring(ResponseStatus.message), RequestUri
| sort by TimeGenerated asc
```
**Triage:** True positive = `alexw@contoso.com` denied a cluster-scope `list secrets` while still reading within `finance` — an actor testing reach. Benign = a misconfigured app hitting a single expected-denied endpoint repeatedly.

### H4 · Suspicious workload created in a sensitive namespace — [T1610](https://attack.mitre.org/techniques/T1610/)
**Hypothesis:** A human principal that `create`s a pod directly (not via a Deployment/controller) in a production namespace — especially a generic/`debug`/`pause` name — may be deploying a foothold or privileged container.
```kusto
AKSAudit
| where Verb == "create" and tostring(ObjectRef.resource) == "pods" and isempty(tostring(ObjectRef.subresource))
| extend actor = tostring(User.username), ns = tostring(ObjectRef.namespace),
         pod = tostring(ObjectRef.name), code = toint(ResponseStatus.code), srcIp = tostring(SourceIps[0])
| where actor !startswith "system:"
| where ns in ("finance","kube-system","default")
| project TimeGenerated, actor, srcIp, ns, pod, code, ua = UserAgent
| sort by TimeGenerated asc
```
**Triage:** True positive = `alexw` creating `pause-debug` in `finance` (code 201) from a Tor-range IP. Benign = a controller principal (excluded) or an approved operator deploying a named, reviewed workload.

## 🔗 Correlates with
- **SigninLogs / AADNonInteractiveUserSignInLogs** on `tostring(User.username)` → `UserPrincipalName` (or `tostring(User.extra.oid[0])` → object id) — tie the in-cluster identity back to the **Entra sign-in** (the risky `185.220.101.2` logon) that obtained cluster credentials.
- **AzureActivity** on `_ResourceId` / `_SubscriptionId` — catch the control-plane operation that handed out access, e.g. `Microsoft.ContainerService/managedClusters/listClusterUserCredential/action`, immediately before the kubectl burst.
- **DeviceNetworkEvents / network tables** on `tostring(SourceIps[0])` → `RemoteIP` — pivot on `185.220.101.2` to see the same attacker IP across the broader incident.
- **AKSAuditAdmin** on `AuditId` — the mutating-only twin; confirm `create`/`delete` events there and de-duplicate the same call seen in both tables.

## 📚 References
- [AKSAudit — Azure Monitor reference](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/aksaudit)
- [AKSAuditAdmin — Azure Monitor reference (mutations-only twin)](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/aksauditadmin)
- [Monitor Azure Kubernetes Service (AKS) control plane / resource logs](https://learn.microsoft.com/en-us/azure/aks/monitor-aks)
- [Kubernetes auditing (upstream) — audit levels and stages](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)
