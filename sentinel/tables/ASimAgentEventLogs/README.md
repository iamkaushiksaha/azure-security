# ASimAgentEventLogs

> **Category:** Security (Microsoft Sentinel — Advanced Security Information Model / ASIM normalized schema)
> **Connector / source:** Sentinel ASIM **Agent** normalization layer. Rows are produced from AI/LLM **agent** telemetry (Azure AI Foundry agents, Microsoft Copilot / Security Copilot–style agents, and other model-and-tool orchestration platforms) ingested into the workspace and projected into the normalized `microsoft.securityinsights/agenteventnormalized` resource type. The "agent" here is an **AI agent**, not a Log Analytics / MMA / AMA host-monitoring agent.
> **Table plan:** **Basic log: Yes** (the reference flags Basic + lake-only ingestion; **Ingestion-time DCR support: No**). Defaults to Analytics only if the workspace explicitly keeps it on the Analytics plan; in most deployments this is a Basic / lake-only table.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/asimagenteventlogs

## What this table is
Each row is a **single normalized AI-agent event** — one interaction in the life of an AI/LLM agent: a model request/response, a tool invocation, an agent-to-agent delegation, or a session/turn boundary. It records **who drove the agent** (`ActorUsername` / `ActorUserId` — the human or service identity), **which agent and platform** ran (`SrcAgentName`, `TargetAgentName`, `PlatformTargetAgentName`), **which model and provider** answered (`ModelName`, `ModelProviderName`), the **generation parameters** (`EventRequestTemperature`, `EventRequestTopP`, `EventRequestSeed`, frequency/presence penalties), **token economics** (`InputTokensUsed`, `OutputTokensUsed`), any **tool** the agent called (`ToolName`, `ToolId`, `ToolDescription`), and the **outcome** (`EventType`, `EventFinishReasons`, `EventErrorDetails`). Rows appear whenever an instrumented agent platform emits events into the workspace. In a SOC it is the primary source for **AI-agent abuse and governance monitoring** — detecting prompt-injection / jailbreak attempts, a compromised identity weaponizing an agent for recon or exfiltration, anomalous tool calls, model/parameter tampering, and agent traffic to attacker infrastructure (`SrcIpAddr`).

## Schema
Full column list, validated against the Microsoft Learn reference. Types are KQL/Log Analytics types.

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | Timestamp (UTC) of when the log was generated / ingested. |
| EventStartTime | datetime | Time at which the agent event started. |
| EventEndTime | datetime | Time at which the agent event ended. |
| EventCount | int | Number of events aggregated into this record. |
| EventType | string | The type of the event (e.g. model request, tool call, session turn). |
| EventOriginalType | string | The original event type as provided by the source. |
| EventOriginalUid | string | Original unique identifier of the event from the source. |
| EventUid | string | A unique identifier for the (normalized) event. |
| EventProduct | string | The product that generated the event. |
| EventVendor | string | The vendor of the product that generated the event. |
| EventSchema | string | Name of the ASIM schema for the event (the `Agent` schema). |
| EventSchemaVersion | string | Version of the ASIM schema used. |
| EventErrorDetails | string | Details about any error that occurred during the event. |
| EventOriginalErrorType | string | The original error type as provided by the source. |
| EventFinishReasons | dynamic | The reason(s) the event/generation completed (e.g. `stop`, `length`, `content_filter`, `tool_calls`). |
| EventOutputType | string | The type of the event output. |
| EventOriginalRequestDetails | string | Original request details as provided by the source. |
| EventOriginalResultDetails | string | Original result details as provided by the source. |
| EventRequestId | string | Unique identifier of the request associated with the event. |
| EventResponseId | string | Unique identifier of the response associated with the event. |
| EventSessionId | string | Unique identifier of the event session (conversation/thread). |
| EventSessionName | string | The name of the event session. |
| EventThoughtProcessId | string | Unique identifier of the reasoning/thought process for the event. |
| EventThoughtProcessDetails | string | Details about the reasoning / chain-of-thought during the event. |
| EventRequestTemperature | real | Temperature sampling parameter used in the request. |
| EventRequestTopP | real | Top-p (nucleus sampling) parameter used in the request. |
| EventRequestSeed | long | Seed parameter used in the request (for reproducibility). |
| EventRequestFrequencyPenalty | real | Frequency-penalty parameter used in the request. |
| EventRequestPresencePenalty | real | Presence-penalty parameter used in the request. |
| ModelName | string | Name of the model used in the event. |
| ModelProviderName | string | Name of the model provider. |
| InputTokensUsed | long | Number of input (prompt) tokens consumed. |
| OutputTokensUsed | long | Number of output (completion) tokens generated. |
| ActorUserId | string | Unique identifier of the actor (identity that invoked the agent). |
| ActorUserIdType | string | Type of the actor user identifier. |
| ActorUsername | string | Username of the actor (e.g. UPN). |
| ActorUsernameType | string | Type of the actor username (e.g. `UPN`, `SAMAccount`). |
| ActorUserScope | string | The scope of the actor user (e.g. tenant). |
| ActorUserScopeId | string | The scope identifier of the actor user. |
| ActingAppId | string | Identifier of the application that initiated the event. |
| ActingAppName | string | Name of the application that initiated the event. |
| ActingAppType | string | Type of the application that initiated the event. |
| SrcAgentId | string | Unique identifier of the **source** agent (the one acting). |
| SrcAgentName | string | Name of the source agent. |
| SrcAgentDescription | string | Description of the source agent. |
| SrcAgentBlueprintId | string | Blueprint (definition) identifier of the source agent. |
| SrcAgentOriginalType | string | Original type of the source agent as reported by the source. |
| SrcFQDN | string | Fully qualified domain name of the source (host running / calling the agent). |
| SrcIpAddr | string | IP address of the source. |
| SrcPortNumber | int | Port number of the source. |
| TargetAgentId | string | Unique identifier of the **target** agent (delegation/hand-off target). |
| TargetAgentName | string | Name of the target agent. |
| TargetAgentDescription | string | Description of the target agent. |
| TargetAgentBlueprintId | string | Blueprint identifier of the target agent. |
| TargetAgentOriginalType | string | Original type of the target agent as reported by the source. |
| TargetAgentUserId | string | User identifier associated with the target agent. |
| TargetAgentUsername | string | Username associated with the target agent. |
| PlatformTargetAgentId | string | Unique identifier of the platform target agent. |
| PlatformTargetAgentName | string | Name of the platform target agent (the hosting agent service). |
| PlatformTargetAgentDescription | string | Description of the platform target agent. |
| PlatformTargetOriginalAgentType | string | Original type of the platform target agent as reported by the source. |
| ToolId | string | Unique identifier of the tool the agent called. |
| ToolName | string | Name of the tool used in the event (function / plugin / skill). |
| ToolDescription | string | Description of the tool used. |
| ToolOriginalType | string | Original type of the tool as reported by the source. |
| AdditionalFields | dynamic | Additional information not covered by other fields, as key-value pairs (nested JSON). |
| SourceSystem | string | Type of agent the event was collected by (`OpsManager` / `Linux` / `Azure`, etc.). |
| TenantId | string | The Log Analytics workspace ID. |
| Type | string | The name of the table. |

> Plus the billing/system columns **`_BilledSize`** (real), **`_IsBillable`** (string), **`_ResourceId`** (string), **`_SubscriptionId`** (string). **Total: 75 columns.** No column has been invented. `AdditionalFields` and `EventFinishReasons` are the only **dynamic/nested** blobs; every other column is a scalar.

## Key columns for detection & hunting
- **Identity:** `ActorUsername` (the invoking principal, typically a UPN — `ActorUsernameType` tells you the format) with `ActorUserId` as the stable id. For delegated/impersonated runs also `TargetAgentUsername` / `TargetAgentUserId`. The calling application is `ActingAppName` / `ActingAppId`.
- **Host / device:** `SrcFQDN` (host that ran or called the agent) and `SrcAgentName` / `PlatformTargetAgentName` (the logical agent identity). There is no generic `DeviceName`/`DeviceId` — agent identity is the primary "asset".
- **Network:** `SrcIpAddr`, `SrcPortNumber`, `SrcFQDN`. No destination IP column — egress destination, where known, lands in `AdditionalFields` or `ToolDescription`.
- **Outcome / result:** **There is no `EventResult` column.** Outcome is inferred from `EventType`, the `EventFinishReasons` dynamic array (e.g. `content_filter` = a guardrail blocked it), and `EventErrorDetails` / `EventOriginalErrorType` on failures.
- **Timestamps:** `TimeGenerated` (ingest) plus the true event window `EventStartTime` → `EventEndTime`. Prefer the event-time columns for latency/duration analysis.
- **Join keys (to other tables):** `ActorUsername` → `UserPrincipalName` (`SigninLogs`, `AADNonInteractiveUserSignInLogs`) and → `AccountUpn`/`AccountName` (`DeviceLogonEvents`, `SecurityEvent`); `SrcIpAddr` → `IPAddress`/`RemoteIP`; `SrcFQDN` → `DeviceName`. `EventSessionId` correlates turns within one agent conversation.

## ⚠️ Schema gotchas
- **AI agent, not host agent.** Despite the name, this table is about **LLM/AI agents**, not Log Analytics monitoring agents. Do not confuse "agent went silent" here with MMA/AMA heartbeat — use `Heartbeat` for collection-agent health.
- **No `EventResult` / success column.** Unlike most ASIM schemas, there is no normalized `EventResult`. Determine success/failure from `EventFinishReasons` (`stop` ≈ normal, `content_filter`/`length`/`tool_calls` ≈ notable) and `EventErrorDetails`. Filtering `EventResult == "Failure"` will fail — the column does not exist.
- **`EventFinishReasons` is a dynamic ARRAY, not a string.** A single completion can finish for multiple reasons. Use `array_index_of(EventFinishReasons, "content_filter") >= 0` or `mv-expand`, not `==`.
- **`ActorUsername` vs `TargetAgentUsername`.** The first is the human/service that invoked the agent; the second is the identity an agent *acts as* downstream. For "who is abusing the agent," pivot on `ActorUsername`; for "what privileges did the agent wield," look at `TargetAgentUsername`.
- **Token and parameter columns are typed `long`/`real`** (`InputTokensUsed`, `OutputTokensUsed`, `EventRequestSeed` are `long`; temperatures/penalties/top-p are `real`). They are genuine numerics — compare and aggregate directly, do not quote them.
- **Basic / lake-only plan caveat.** The reference marks **Basic log: Yes** and **Lake-only ingestion: Yes** with **no ingestion-time DCR**. Under Basic/lake plans, scheduled-analytics rules and cross-table `join` are restricted — confirm the workspace plan before building alerting on this table.

## 🧪 Sample data
[`ASimAgentEventLogs_sample.csv`](ASimAgentEventLogs_sample.csv) — 23 rows. The rows tell the **Operation Quiet Ledger** AI-agent angle: during the same morning, the compromised analyst `alexw@contoso.com` (and the abused `svc-backup@contoso.com` automation identity) drive the corporate **FinanceCopilot** agent on **FIN-WS-07** through a series of escalating, off-pattern requests — recon prompts, a **prompt-injection** turn that a `content_filter` blocks, tool calls that enumerate `stcontosofin` storage and read `kv-contoso-prod` secrets, and finally an agent run sourced from attacker IP `185.220.101.2`; a parallel Linux **DevOpsAgent** on **WEB-APP-01** is coaxed into a shell-exec tool call. Benign analyst and admin agent usage by `meganb`, `jamest`, `dvora` and `itadmin` runs throughout as noise. This is the **AI-agent-abuse facet** of the cross-table scenario, spanning the 08:20→11:00 window (recon → priv-esc → storage/keyvault exfil).
The sample uses this curated subset of **real** columns: `TimeGenerated`, `EventType`, `ActorUsername`, `ActorUsernameType`, `SrcAgentName`, `PlatformTargetAgentName`, `ModelName`, `ModelProviderName`, `InputTokensUsed`, `OutputTokensUsed`, `EventRequestTemperature`, `EventFinishReasons`, `EventErrorDetails`, `ToolName`, `ToolDescription`, `SrcFQDN`, `SrcIpAddr`, `EventSessionId`, `AdditionalFields`.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · Guardrail-blocked turns — prompt injection / jailbreak — [T1059](https://attack.mitre.org/techniques/T1059/)
**Hypothesis:** An agent turn whose `EventFinishReasons` contains `content_filter` (or that carries an `EventErrorDetails` jailbreak signal) is the model refusing a manipulated/unsafe prompt — a probe for prompt injection or jailbreak.
```kusto
ASimAgentEventLogs
| where array_index_of(EventFinishReasons, "content_filter") >= 0
    or EventErrorDetails has_any ("jailbreak", "prompt injection", "policy")
| project TimeGenerated, ActorUsername, SrcAgentName, ToolName, EventErrorDetails, EventFinishReasons, SrcIpAddr
| sort by TimeGenerated asc
```
**Triage:** True positive = repeated blocked turns from one `ActorUsername`/`EventSessionId` (here `alexw` probing FinanceCopilot), especially around sensitive tools. Benign = an isolated false-trigger on legitimate content.

### H2 · Agent tool calls that touch sensitive resources — [T1213](https://attack.mitre.org/techniques/T1213/)
**Hypothesis:** Agent tool invocations enumerating storage or reading secrets (`ToolName`/`ToolDescription` referencing storage keys, blobs, or Key Vault) by a non-routine actor indicate data-staging via the agent.
```kusto
ASimAgentEventLogs
| where EventType == "ToolCall"
| where ToolName has_any ("Storage", "Blob", "KeyVault", "Secret")
    or ToolDescription has_any ("storage", "blob", "secret", "key vault")
| summarize Calls = count(), Tools = make_set(ToolName), FirstSeen = min(TimeGenerated), LastSeen = max(TimeGenerated)
        by ActorUsername, SrcAgentName, EventSessionId
| sort by Calls desc
```
**Triage:** True positive = `alexw` / `svc-backup` driving FinanceCopilot to list `stcontosofin` keys and read `kv-contoso-prod` secrets in one session. Benign = a sanctioned data-analysis agent the actor uses daily.

### H3 · Agent invoked from an external / attacker IP — [T1078.004](https://attack.mitre.org/techniques/T1078/004/)
**Hypothesis:** An agent event whose `SrcIpAddr` is an untrusted public address (not corporate egress) means the agent was driven from outside the estate on a known identity — session hijack or stolen token.
```kusto
ASimAgentEventLogs
| where isnotempty(SrcIpAddr)
| where SrcIpAddr !in ("52.170.12.45", "20.98.111.30") and SrcIpAddr !startswith "10."
| project TimeGenerated, ActorUsername, SrcAgentName, SrcFQDN, SrcIpAddr, EventType, ToolName
| sort by TimeGenerated asc
```
**Triage:** True positive = FinanceCopilot driven as `alexw` from `185.220.101.2`/`91.219.236.18`. Benign = a new but legitimate corporate NAT egress — confirm the IP against the approved egress list.

### H4 · Anomalous generation parameters — model/parameter tampering — [T1565.001](https://attack.mitre.org/techniques/T1565/001/)
**Hypothesis:** Requests pushed to an unusually high `EventRequestTemperature` (more random, guardrail-evasive output) on a sensitive agent can indicate an attacker tuning the model to bypass deterministic safety behaviour.
```kusto
ASimAgentEventLogs
| where EventRequestTemperature >= 1.5
| project TimeGenerated, ActorUsername, SrcAgentName, ModelName, EventRequestTemperature, EventFinishReasons, SrcIpAddr
| sort by EventRequestTemperature desc
```
**Triage:** True positive = a normally low-temperature finance agent suddenly run near max temperature by `alexw`. Benign = a creative/brainstorming agent where high temperature is expected.

## 🔗 Correlates with
- **SigninLogs** on `ActorUsername` → `UserPrincipalName` (and `SrcIpAddr` → `IPAddress`) — tie the agent abuse back to `alexw`'s 08:20 risky sign-in from NL and confirm the same attacker IP drove both.
- **DeviceLogonEvents / DeviceProcessEvents** on `SrcFQDN` → `DeviceName` — confirm the agent ran on **FIN-WS-07** during the same window the host was compromised, and see the local process that launched it.
- **StorageBlobLogs / AzureActivity** on `ActorUsername` and resource (`stcontosofin`, `kv-contoso-prod`) — corroborate that the storage-enumeration and secret-read **tool calls** turned into real control-plane / data-plane operations (10:00 key list → 10:20 blob exfil → 10:40 Key Vault).
- **Heartbeat** on `SrcFQDN` → `Computer` — *governance contrast:* if a **collection** agent on FIN-WS-07 went silent during the incident window while the **AI** agent stayed busy, that gap is a defense-evasion / log-tampering tell ([T1562.001](https://attack.mitre.org/techniques/T1562/001/)); use `Heartbeat`, not this table, to detect the silenced sensor.

## 📚 References
- [ASimAgentEventLogs — Azure Monitor reference](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/asimagenteventlogs)
- [Queries for the ASimAgentEventLogs table — Azure Monitor reference](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/queries/asimagenteventlogs)
- [Advanced Security Information Model (ASIM) overview — Microsoft Sentinel](https://learn.microsoft.com/en-us/azure/sentinel/normalization)
