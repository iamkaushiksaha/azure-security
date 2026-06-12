# Schema validation & ASIM normalization

Wrong column name or type = wrong/empty results, no error. This is the validation protocol and the
normalization layer that make queries portable.

## Validation protocol (run before finalizing any query)

1. **Confirm the table exists** and you have the right one. Beware near-twins: `SecurityEvent`
   (Windows Security log) vs `Event` (System/Application); `SecurityAlert` (Sentinel/Defender) vs
   `Alert` (legacy Azure Monitor); `DnsEvents` (queries) vs `DnsAuditEvents` (config changes);
   `AKSAudit` (all) vs `AKSAuditAdmin` (no get/list/watch).
2. **Confirm every column name + type** against the [in-repo table library](../../../../sentinel/tables/README.md)
   first, then MS Learn `…/reference/tables/<tablename>`, then live `<Table> | getschema`.
3. **Identify dynamic/nested columns** and plan the drill-down + cast.
4. **Check the table plan** (Analytics / Basic / Auxiliary) — it limits operators, alerting, and
   retention (see [sentinel-architecture.md](sentinel-architecture.md)).
5. **Flag the unverifiable** with `// ⚠️ unverified: <col>` instead of guessing.

## The type & location traps that bite (memorize)

| Trap | Reality |
|---|---|
| `SigninLogs.ResultType` | **string** `"0"`, not int |
| `AuditLogs` identity | inside dynamic `InitiatedBy` → `tostring(InitiatedBy.user.userPrincipalName)` |
| `AuditLogs.TargetResources` | dynamic **array** → `[0].displayName` or `mv-expand` |
| `OfficeActivity` identity | `UserId` (no `UserPrincipalName` column); IP split across `ClientIP`/`Client_IPAddress`/`ActorIpAddress`; outcome `ResultStatus`; workload `OfficeWorkload` |
| `AzureActivity` | outcome `ActivityStatusValue` (string twins `ActivityStatus` are deprecated); identity `Caller`; rich data in `Authorization_d`/`Claims_d`/`Properties_d` |
| `AzureDiagnostics` | schema-on-read; type-suffixed columns `_s`/`_d`/`_b`/`_g`/`_t`; identity varies by provider |
| `SecurityEvent` | source IP is `IpAddress` (not `SourceIP`); `Status`/`SubStatus` are hex **strings**; correlation is `Correlation` (no `Id`); success/fail = EventID 4624/4625 |
| `StorageBlobLogs` | `StatusCode` is a **string**; `CallerIpAddress` includes `:port`; identity only on OAuth |
| `AKSAudit`/`Admin` | identity/IPs/object/result all in **dynamic** blobs; `pods/exec` success = HTTP **101** |
| `DnsEvents` | `IPAddresses` is a comma **string**; `Computer` is the DNS *server*, client is `ClientIP` |
| `DnsAuditEvents` | **no actor column** — attribute via `SecurityEvent` 4662/5136 |
| `Heartbeat` | `ComputerIP` is the *public* IP; detection value is in *gaps*, not rows |
| `Syslog`/`LinuxAuditLog` | identity/cmd/outcome embedded in `SyslogMessage` / lowercase auditd fields (`acct`,`exe`,`res`) — `parse`/`extract` |

The per-table docs in the library spell each of these out with examples.

## ASIM — write once, match every source

The **Advanced Security Information Model** gives Sentinel a normalized schema per activity type
(Authentication, NetworkSession, Dns, ProcessEvent, FileEvent, WebSession, …), exposed through
**unifying parsers**. One ASIM query covers every source that has a parser for that schema —
portable and future-proof.

**Conventions that trip people up:**
- **Parser name has a leading underscore:** `_Im_Authentication`, `_Im_Dns`, `_Im_NetworkSession`
  (the built-in, optimized form). `Im_*` (no underscore) and `ASim*`/`vim*` variants exist — prefer
  `_Im_*` for performance.
- **Call parameters are lowercase** and filter *before* parsing for speed:
  `starttime=`, `endtime=`, `eventresult=`, `responsecodename=`, `srcipaddr=`.
- **Output fields are PascalCase:** `SrcIpAddr`, `TargetUserId`, `EventResult`, `ResponseCodeName`.

```kusto
// Failed auth across every identity source that has an ASIM parser
_Im_Authentication(starttime=ago(1h), eventresult='Failure')
| summarize Failures = count() by TargetUserId, SrcIpAddr
| sort by Failures desc
```

```kusto
// Normalized DNS NXDOMAIN beaconing — filter params lowercase, run before parse
_Im_Dns(starttime=ago(1d), responsecodename='NXDOMAIN')
| summarize count() by SrcIpAddr, bin(TimeGenerated, 15m)
```

**When to use ASIM vs raw tables:** ASIM for portable detections that should span sources and
survive a connector change; raw tables for one-off exploration, source-specific fields ASIM doesn't
carry, or where no parser exists. Always pass at least `starttime=`.

> The `ASimAgentEventLogs` *table* is unrelated to these parsers — despite the "ASim" prefix it is
> the normalized **AI/LLM agent** telemetry table, not an ASIM activity schema.

References: [ASIM overview](https://learn.microsoft.com/en-us/azure/sentinel/normalization) ·
[Use ASIM parsers](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers) ·
[ASIM schemas](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-schemas) ·
[Table references](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables-category)
