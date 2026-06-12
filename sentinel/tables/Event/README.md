# Event

> **Category:** Security, Virtual Machines (Azure Monitor; solution **LogManagement**)
> **Connector / source:** Windows **System & Application (and other non-Security) event logs** collected from monitored Windows hosts by the **Log Analytics / MMA agent** or the **Azure Monitor Agent (AMA)** via a *Windows Event Logs* data-collection rule. (The Windows **Security** log is routed to `SecurityEvent`, **not** here.)
> **Table plan:** Analytics (default). Ingestion-time DCR transforms supported; Basic logs = No, lake-only = No.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/event

## What this table is
Each row is a single **Windows Event Log record** from a log *other than* Security — most commonly the **System** and **Application** logs (also Setup, DNS Server, PowerShell/Operational, etc.). The originating log is in **`EventLog`**, the publisher/provider is **`Source`**, and the Windows event number is **`EventID`**. Rows appear whenever a matching event is written on a monitored host and the agent's DCR/collection config forwards that log + event ID to the workspace. In a SOC this table is the workhorse for **service-based persistence** (System log `Service Control Manager` **7045** new-service-installed, **7034/7031** unexpected service stop), **endpoint AV telemetry** (Application log `Microsoft-Windows-Windows Defender` **1116/1117** malware detected/remediated), and **application-stability / crash hunting** (Application Error **1000**) — context that the Security-audit channel (`SecurityEvent`) does not carry.

## Schema
Full column list, validated against the Microsoft Learn reference. The Event table is narrow (22 columns) — every column is listed individually.

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | Date and time the record was created (UTC). |
| Source | string | **Source / publisher of the event** (e.g. `Service Control Manager`, `Microsoft-Windows-Windows Defender`, `Application Error`, `EventLog`). This is the Windows event *provider*. |
| EventLog | string | **Name of the event log the record was collected from** (e.g. `System`, `Application`, `Setup`). |
| EventID | int | **Number of the event** (the Windows event id, e.g. 7045, 1116, 1000). |
| EventLevel | int | Severity of the event in **numeric** form (1 Critical, 2 Error, 3 Warning, 4 Information, 5 Verbose). |
| EventLevelName | string | Severity of the event in **text** form (`Information`, `Warning`, `Error`, `Critical`, `Verbose`). |
| EventCategory | int | Category of the event (provider-defined task/category number). |
| RenderedDescription | string | **Human-readable event message with parameter values substituted in** — the rendered description shown in Event Viewer. |
| Message | string | Event message for the different languages (language set by the LCID attribute). Often mirrors `RenderedDescription`. |
| ParameterXml | string | Event parameter values in **XML** format (the raw `<Param>` insertion strings). |
| EventData | string | All event data in **raw** format (the full EventData blob). |
| Computer | string | Name of the **computer** the event was collected from (the host). |
| UserName | string | User name of the account that logged the event (often `N/A` / a machine account for System-log events). |
| Role | string | Role of the cloud service the log belongs to. Only populated when collected via Azure Diagnostics from Azure storage. |
| AzureDeploymentID | string | Azure deployment ID of the cloud service. Only populated for Azure Diagnostics collection from storage. |
| ManagementGroupName | string | Name of the SCOM management group; for other agents this is `AOI-<workspace ID>`. |
| SourceSystem | string | Type of agent that collected the event (`OpsManager` for the Windows agent, `Azure` for Azure Diagnostics). |
| Type | string | The name of the table (`Event`). |
| _ResourceId | string | Azure resource ID the record is associated with. |
| _SubscriptionId | string | Subscription ID the record is associated with. |
| _BilledSize | real | The record size in bytes. |
| _IsBillable | string | Whether ingesting the record is billable (`true`/`false` as a **string**). |

## Key columns for detection & hunting
- **Identity:** `UserName` — the account that logged the event where present. Many System-log events (e.g. `Service Control Manager`) carry **no user** (`N/A` / `NT AUTHORITY\SYSTEM`); for those, identity is inferred from the *content* (e.g. the service binary path in `RenderedDescription`), not a dedicated column.
- **Host / device:** `Computer` (the host the event came from).
- **Network:** n/a — this table has no IP/port columns. Network indicators live inside `RenderedDescription` / `EventData` for the few providers that log them.
- **Outcome / result:** There is no boolean result column. Severity is `EventLevel` (int) / `EventLevelName` (string); the *meaning* of an event is the **(`EventLog`, `Source`, `EventID`)** triple plus the text in `RenderedDescription`.
- **Timestamps:** `TimeGenerated` (UTC). There is no separate event-time column.
- **Join keys (to other tables / within table):** `Computer` (↔ `SecurityEvent.Computer`, `Heartbeat.Computer`, `DeviceEvents.DeviceName`), `UserName` where populated, and the logical key **`Source` + `EventID`** to bucket event types.

## ⚠️ Schema gotchas
- **This is NOT the Security log.** Windows **Security** events (4624/4625/4688/7045-style audit) go to **`SecurityEvent`**. `Event` carries System, Application, Setup, DNS, etc. Don't hunt 4624 here.
- **The log name is `EventLog`, the provider is `Source`, and they are different things.** `EventLog == "System"` is the channel; `Source == "Service Control Manager"` is the publisher within it. Filtering only on `EventID` across all sources is ambiguous (the same id means different things in different providers).
- **`EventID` and `EventLevel`/`EventCategory` are `int`** — don't quote them. But **`_IsBillable` is a `string`** (`"true"`/`"false"`), not a bool.
- **The message lives in `RenderedDescription`** (rendered, parameters substituted). `Message` is the localized form, while `ParameterXml` and `EventData` hold the *raw* insertion strings — query `RenderedDescription` for human-readable hunting, fall back to `EventData`/`ParameterXml` for fields not surfaced as columns.
- **`UserName` is frequently empty / `N/A`** for System-log and service events. Absence of a user is normal here — don't treat it as a parsing error.
- **Many events are benign by design.** Service starts/stops and application info events are high-volume noise; detections must pin the **(`Source`,`EventID`)** pair *and* inspect `RenderedDescription` (e.g. the service image path) to separate signal.

## 🧪 Sample data
[`Event_sample.csv`](Event_sample.csv) — 24 rows. The rows tell the **Windows host-log side of *Operation Quiet Ledger* (~09:25–09:55)**: a malicious service is installed on the domain controller for persistence (System log, `Service Control Manager` **7045**, image path under `C:\Windows\Temp\svc-update.exe`) on **DC01**, **Windows Defender** detects and then remediates a dropped payload on **FIN-WS-07** (Application log, `Microsoft-Windows-Windows Defender` **1116** then **1117**), a service crashes unexpectedly on FIN-WS-07 (System `Service Control Manager` **7034** + Application `Application Error` **1000**) — interleaved with routine System/Application info events (service installs/starts, Group Policy, MsiInstaller, .NET Runtime) from **HR-WS-03** and benign hosts.
The sample uses this curated subset of **real** columns: `TimeGenerated`, `Source`, `EventLog`, `EventID`, `EventLevel`, `EventLevelName`, `EventCategory`, `RenderedDescription`, `Computer`, `UserName`, `SourceSystem`, `Type`. This is the **service-persistence + endpoint-AV step** of the cross-table attack scenario; pivot on `Computer` into `SecurityEvent` (4688/4720 on the same hosts) and `Heartbeat`.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · Suspicious new service installed — [T1543.003](https://attack.mitre.org/techniques/T1543/003/)
**Hypothesis:** A `Service Control Manager` **7045** (new service installed) whose image path lives in a world-writable / temp directory (`\Temp\`, `\Users\`, `\ProgramData\`) is service-based persistence, not a legitimate product install.
```kusto
Event
| where EventLog == "System" and Source == "Service Control Manager" and EventID == 7045
| where RenderedDescription has_any (@"\Windows\Temp\", @"\Users\", @"\ProgramData\", @"\AppData\", "powershell", "cmd.exe", "-enc")
| project TimeGenerated, Computer, UserName, EventID, RenderedDescription
| sort by TimeGenerated asc
```
**Triage:** True positive = an unfamiliar service name with a binary in `C:\Windows\Temp` (e.g. `svc-update.exe`) on a domain controller. Benign = vendor agents (`Microsoft Monitoring Agent`, EDR) installing under `C:\Program Files`.

### H2 · Windows Defender malware detection — [T1204.002](https://attack.mitre.org/techniques/T1204/002/)
**Hypothesis:** A `Microsoft-Windows-Windows Defender` **1116** (malware detected) — especially followed by **1117** (action taken) — on a finance workstation indicates a delivered/executed payload.
```kusto
Event
| where Source == "Microsoft-Windows-Windows Defender" and EventID in (1116, 1117)
| project TimeGenerated, Computer, EventID, EventLevelName, RenderedDescription
| sort by Computer asc, TimeGenerated asc
```
**Triage:** True positive = a real threat name (e.g. `Trojan:Win32/…`) detected in a user/temp path on FIN-WS-07 with action `Quarantine`/`Remove`. Benign = EICAR test files or detections inside isolated lab/quarantine folders.

### H3 · Service crash / unexpected termination — [T1489](https://attack.mitre.org/techniques/T1489/)
**Hypothesis:** A `Service Control Manager` **7034** (service terminated unexpectedly) or **7031**, correlated with an `Application Error` **1000** on the same host, can indicate process injection, a crashing implant, or defensive tooling being killed.
```kusto
Event
| where (Source == "Service Control Manager" and EventID in (7031, 7034))
     or (Source == "Application Error" and EventID == 1000)
| project TimeGenerated, Computer, EventLog, Source, EventID, EventLevelName, RenderedDescription
| sort by Computer asc, TimeGenerated asc
```
**Triage:** True positive = a security service crashing on the same host/timeframe as other suspicious activity. Benign = an occasional app fault on a workstation with no surrounding indicators.

### H4 · Error/Critical events bursting on one host — [T1499](https://attack.mitre.org/techniques/T1499/)
**Hypothesis:** A spike of `Error`/`Critical` System+Application events on a single host in a short window is worth a look (instability from exploitation, mass service failure, or resource exhaustion).
```kusto
Event
| where EventLevelName in ("Error", "Critical")
| summarize Errors = count(), Sources = make_set(Source), Ids = make_set(EventID), FirstSeen = min(TimeGenerated), LastSeen = max(TimeGenerated)
        by Computer
| where Errors >= 2
| sort by Errors desc
```
**Triage:** True positive = several distinct error sources clustering on a host already implicated by other tables. Benign = a single noisy application repeatedly logging the same fault.

## 🔗 Correlates with
- **SecurityEvent** on `Computer` — pivot from the 7045 service-install / Defender detection here to the matching **4688** process-creation and **4720** account-creation on the same DC01 / FIN-WS-07 in the Security log.
- **Heartbeat** on `Computer` — confirm the host (DC01, FIN-WS-07) was reporting around the event window, or stopped after the crash.
- **DeviceEvents / DeviceProcessEvents** on `Computer` ↔ `DeviceName` — corroborate the Windows-host view with Defender for Endpoint telemetry (the dropped binary, the service-create action) on FIN-WS-07.
- **SecurityAlert** on `Computer` — line up the Defender AV detection (1116/1117) with the Sentinel/Defender alert it raises for the same host.

## 📚 References
- Event table reference — https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/event
- Collect Windows event logs with Azure Monitor Agent — https://learn.microsoft.com/en-us/azure/azure-monitor/agents/data-collection-windows-events
- Windows Defender Antivirus event IDs (1116/1117) — https://learn.microsoft.com/en-us/defender-endpoint/troubleshoot-microsoft-defender-antivirus
