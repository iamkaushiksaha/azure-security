# DeviceProcessEvents

> **Category:** Microsoft Defender XDR (Microsoft Defender for Endpoint) — Security
> **Connector / source:** Microsoft Defender for Endpoint (MDE) advanced hunting, streamed to Microsoft Sentinel via the *Microsoft Defender XDR* connector. Each row is emitted by the MDE sensor on an onboarded endpoint when a process is created.
> **Table plan:** Basic supported (the page flags **Basic log: Yes**, plus ingestion-time DCR and lake-only ingestion); commonly ingested as Analytics for full KQL + analytics-rule support.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/deviceprocessevents

## What this table is
Each row is a single **process-creation** event observed on a Defender for Endpoint–onboarded device — the MDE/advanced-hunting equivalent of Windows Security event 4688 (and Sysmon Event ID 1), but richer. For every spawned process the sensor records the **created process** (image name, folder path, full command line, hashes, PID, integrity level, signer/version metadata) **and** the **process that created it** (`InitiatingProcess*`) together with **that** process's parent (`InitiatingProcessParent*`) and the **account context** it all ran as. `ActionType` is `ProcessCreated`. In a SOC this is the process-tree backbone of the endpoint story: it is the primary table for hunting suspicious parent→child chains (Office → script host), encoded/obfuscated PowerShell, LOLBin abuse (`rundll32`, `mshta`, `regsvr32`), dropper execution, and credential-dumper launches — and it stitches file, network, and logon telemetry together by device and time.

## Schema
Full column list, validated against the Microsoft Learn reference. (Types are the KQL/Log Analytics types: string, int, long, real, datetime, bool, dynamic, guid.)

| Column | Type | Description |
|---|---|---|
| AccountDomain | string | Domain of the account (the account context of the **created** process). |
| AccountName | string | User name of the account. |
| AccountObjectId | string | Unique identifier for the account in Microsoft Entra ID. |
| AccountSid | string | Security Identifier (SID) of the account. |
| AccountUpn | string | User principal name (UPN) of the account. |
| ActionType | string | Type of activity that triggered the event. For this table the value is `ProcessCreated`. |
| AdditionalFields | dynamic | Additional information about the entity or event (JSON blob). |
| AppGuardContainerId | string | Identifier for the virtualized container used by Application Guard to isolate browser activity. |
| _BilledSize | real | The record size in bytes. |
| CreatedProcessSessionId | long | Windows session ID of the created process. |
| DeviceId | string | Unique identifier for the device in the service (stable GUID; prefer for joins). |
| DeviceName | string | Fully qualified domain name (FQDN) of the device. |
| FileName | string | Name of the file that the recorded action was applied to — i.e. the image of the **created** process. |
| FileSize | long | Size of the file (created process image) in bytes. |
| FolderPath | string | Folder containing the file (image) of the created process. |
| InitiatingProcessAccountDomain | string | Domain of the account that ran the process responsible for the event. |
| InitiatingProcessAccountName | string | User name of the account that ran the process responsible for the event. |
| InitiatingProcessAccountObjectId | string | Microsoft Entra object ID of the user account that ran the process responsible for the event. |
| InitiatingProcessAccountSid | string | Security Identifier (SID) of the account that ran the process responsible for the event. |
| InitiatingProcessAccountUpn | string | User principal name (UPN) of the account that ran the process responsible for the event. |
| InitiatingProcessCommandLine | string | Command line used to run the process that initiated the event (the parent/creator command line). |
| InitiatingProcessCreationTime | datetime | Date and time when the process that initiated the event was started. |
| InitiatingProcessFileName | string | Name of the process that initiated the event (the immediate parent of the created process). |
| InitiatingProcessFileSize | long | Size in bytes of the file (image) that ran the process responsible for the event. |
| InitiatingProcessFolderPath | string | Folder containing the process (image file) that initiated the event. |
| InitiatingProcessId | long | Process ID (PID) of the process that initiated the event. |
| InitiatingProcessIntegrityLevel | string | Integrity level of the initiating process (e.g. `Low`, `Medium`, `High`, `System`). Influenced by characteristics such as launch from an internet download. |
| InitiatingProcessLogonId | long | Identifier for a logon session of the initiating process. Unique on the same machine only between restarts. |
| InitiatingProcessMD5 | string | MD5 hash of the process (image file) that initiated the event. |
| InitiatingProcessParentCreationTime | datetime | Date and time when the parent of the process responsible for the event was started. |
| InitiatingProcessParentFileName | string | Name of the **parent** process that spawned the process responsible for the event (the grandparent of the created process). |
| InitiatingProcessParentId | long | Process ID (PID) of the parent process that spawned the process responsible for the event. |
| InitiatingProcessRemoteSessionDeviceName | string | Device name of the remote device from which the initiating process's RDP session was initiated. |
| InitiatingProcessRemoteSessionIP | string | IP address of the remote device from which the initiating process's RDP session was initiated. |
| InitiatingProcessSessionId | long | Windows session ID of the initiating process. |
| InitiatingProcessSHA1 | string | SHA-1 hash of the process (image file) that initiated the event. |
| InitiatingProcessSHA256 | string | SHA-256 hash of the initiating process image. **In some cases not populated — fall back to `InitiatingProcessSHA1`.** |
| InitiatingProcessSignatureStatus | string | Signature status of the process (image file) that initiated the event (e.g. `Valid`, `Invalid`, `Unsigned`). |
| InitiatingProcessSignerType | string | Type of file signer of the process (image file) that initiated the event. |
| InitiatingProcessTokenElevation | string | Token type indicating presence/absence of UAC privilege elevation applied to the initiating process. |
| InitiatingProcessUniqueId | string | Unique identifier of the initiating process; equals the Process Start Key on Windows devices. |
| InitiatingProcessVersionInfoCompanyName | string | Company name from the version information of the initiating process image. |
| InitiatingProcessVersionInfoFileDescription | string | Description from the version information of the initiating process image. |
| InitiatingProcessVersionInfoInternalFileName | string | Internal file name from the version information of the initiating process image. |
| InitiatingProcessVersionInfoOriginalFileName | string | Original file name from the version information of the initiating process image. |
| InitiatingProcessVersionInfoProductName | string | Product name from the version information of the initiating process image. |
| InitiatingProcessVersionInfoProductVersion | string | Product version from the version information of the initiating process image. |
| _IsBillable | string | Specifies whether ingesting the data is billable. When `false`, ingestion isn't billed to your Azure account. |
| IsInitiatingProcessRemoteSession | bool | Whether the initiating process ran under an RDP session (`true`) or locally (`false`). |
| IsProcessRemoteSession | bool | Whether the **created** process ran under an RDP session (`true`) or locally (`false`). |
| LogonId | long | Identifier for a logon session (of the created process). Unique on the same machine only between restarts. |
| MachineGroup | string | Machine group of the machine, used by RBAC to determine access to the machine. |
| MD5 | string | MD5 hash of the file (created process image). |
| ProcessCommandLine | string | Command line used to create the new process. |
| ProcessCreationTime | datetime | Date and time the process was created. |
| ProcessId | long | Process ID (PID) of the newly created process. |
| ProcessIntegrityLevel | string | Integrity level of the newly created process (e.g. `Low`, `Medium`, `High`, `System`). |
| ProcessRemoteSessionDeviceName | string | Device name of the remote device from which the created process's RDP session was initiated. |
| ProcessRemoteSessionIP | string | IP address of the remote device from which the created process's RDP session was initiated. |
| ProcessTokenElevation | string | Token type indicating presence/absence of UAC privilege elevation applied to the newly created process. |
| ProcessUniqueId | string | Unique identifier of the created process; equals the Process Start Key on Windows devices. |
| ProcessVersionInfoCompanyName | string | Company name from the version information of the newly created process. |
| ProcessVersionInfoFileDescription | string | Description from the version information of the newly created process. |
| ProcessVersionInfoInternalFileName | string | Internal file name from the version information of the newly created process. |
| ProcessVersionInfoOriginalFileName | string | Original file name from the version information of the newly created process. |
| ProcessVersionInfoProductName | string | Product name from the version information of the newly created process. |
| ProcessVersionInfoProductVersion | string | Product version from the version information of the newly created process. |
| ReportId | long | Event identifier based on a repeating counter. Unique only in conjunction with the device and event time. |
| SHA1 | string | SHA-1 hash of the file (created process image). |
| SHA256 | string | SHA-256 hash of the file (created process image). |
| SourceSystem | string | The type of agent the event was collected by (e.g. `OpsManager`, `Linux`, `Azure`). |
| TenantId | string | The Log Analytics workspace ID. |
| TimeGenerated | datetime | Date and time the event was recorded by the MDE agent on the endpoint. |
| Type | string | The name of the table. |

> All 78 columns from the reference page are listed above; none are grouped or omitted.

## Key columns for detection & hunting
- **Identity (actor):** `AccountName` / `AccountUpn` / `AccountSid` describe the account the **created** process runs as; `InitiatingProcessAccountName` / `InitiatingProcessAccountUpn` / `InitiatingProcessAccountSid` describe the account that **launched** it. They usually match, but a privilege-escalation/impersonation chain is exactly where they diverge — project both.
- **Host / device:** `DeviceName` (FQDN) and `DeviceId` (stable GUID — prefer for joins; survives renames).
- **Network:** No local socket columns. RDP provenance only: `ProcessRemoteSessionIP` / `ProcessRemoteSessionDeviceName` (created process) and `InitiatingProcessRemoteSessionIP` / `InitiatingProcessRemoteSessionDeviceName` (initiating process), populated when `IsProcessRemoteSession` / `IsInitiatingProcessRemoteSession` is `true`. For real network context pivot to `DeviceNetworkEvents`.
- **Outcome / result:** No success/failure column — the event *is* the outcome (a process was created). `ActionType` is always `ProcessCreated` for this table; semantics come from the command line, image, hashes, and the parent chain.
- **Timestamps:** `TimeGenerated` (recorded by the MDE agent). Process-context times: `ProcessCreationTime` (created), `InitiatingProcessCreationTime` (parent), `InitiatingProcessParentCreationTime` (grandparent). There is **no** separate `EventTime` column despite the `ReportId` description implying one.
- **Join keys (to other tables):** `DeviceId` / `DeviceName` (to all `Device*` tables); `SHA256` / `SHA1` / `MD5` of the created image (to `DeviceFileEvents`, file reputation); `ProcessId` + `ProcessCreationTime` (to child events as their `InitiatingProcessId` + `InitiatingProcessCreationTime`); `InitiatingProcessId` + `InitiatingProcessCreationTime` (back up the tree); `AccountSid` / `AccountUpn` / `InitiatingProcessAccountSid` (to identity tables, `DeviceLogonEvents`, `SecurityEvent`).

## ⚠️ Schema gotchas
- **Three process layers, named asymmetrically.** The created process uses bare `FileName` / `FolderPath` / `ProcessCommandLine` / `ProcessId` (no `Process` prefix on `FileName`/`FolderPath`). Its parent is `InitiatingProcess*`. The parent's parent is `InitiatingProcessParent*` — and `InitiatingProcessParent*` exposes **only** `FileName`, `Id`, and `CreationTime` (no command line, no hashes). Don't expect a grandparent command line in this table.
- **No `EventTime` or `ComputerName` column** even though the `ReportId` description references them. Identify a unique event with `TimeGenerated` + `DeviceName`/`DeviceId` + `ReportId`.
- **`InitiatingProcessSHA256` is often empty** — Microsoft's note says to fall back to `InitiatingProcessSHA1`. Don't key detections solely on the initiating-process SHA256. (The created-process `SHA256` is reliably populated.)
- **`_IsBillable` is a *string*, not a bool** (`"true"`/`"false"`); the `IsProcessRemoteSession` / `IsInitiatingProcessRemoteSession` columns *are* real `bool`s. Compare each with the correct literal type.
- **`AccountName` ≠ `InitiatingProcessAccountName`.** A query that uses only `AccountName` describes the spawned process's identity, not the launcher's. For "who ran this", `InitiatingProcessAccountName` is usually what you want.
- **Command lines are verbatim and case/quote-sensitive.** Encoded PowerShell may appear as `-enc`, `-EncodedCommand`, `-e`, `-ec`, etc., and base64 casing varies — match case-insensitively with `has_any`/`matches regex`, not exact equality.

## 🧪 Sample data
[`DeviceProcessEvents_sample.csv`](DeviceProcessEvents_sample.csv) — 30 rows. On **FIN-WS-07** (~08:40–09:15) the compromised user **alexw** runs the malicious process tree: `WINWORD.EXE` (opening a phishing attachment) spawns `powershell.exe -enc <base64>`, which spawns LOLBins `rundll32.exe` and `mshta.exe`, drops and runs `SecurityUpdate_KB5039211.exe`, launches the renamed credential dumper `svchost_helper.exe` (`sekurlsa`), and archives staged finance files with `7z.exe` — interleaved with benign processes on **HR-WS-03** (Word/Edge) and **DC01** (scheduled tasks, `lsass`) for signal-vs-noise.
The sample uses this curated subset of **real** columns: `TimeGenerated`, `DeviceName`, `DeviceId`, `ActionType`, `FileName`, `FolderPath`, `ProcessCommandLine`, `SHA256`, `ProcessId`, `ProcessIntegrityLevel`, `AccountName`, `InitiatingProcessFileName`, `InitiatingProcessCommandLine`, `InitiatingProcessParentFileName`, `InitiatingProcessAccountName`, `InitiatingProcessAccountUpn`, `InitiatingProcessAccountSid`, `InitiatingProcessId`, `ReportId`. This is the **process-execution / tooling-run** step of *Operation Quiet Ledger* (the ~09:00 "tooling dropped and run" stage on FIN-WS-07, between the device logon and the C2/lateral-movement stages); SHA256 and `DeviceId` values line up with the `DeviceFileEvents` sample.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · Office application spawning a script host — [T1566](https://attack.mitre.org/techniques/T1566/) → [T1059](https://attack.mitre.org/techniques/T1059/)
**Hypothesis:** A phishing document executes code by having an Office app (`winword.exe`/`excel.exe`/`powerpnt.exe`) launch a script interpreter or LOLBin (`powershell.exe`, `cmd.exe`, `wscript.exe`, `mshta.exe`, `rundll32.exe`).
```kusto
DeviceProcessEvents
| where ActionType == "ProcessCreated"
| where InitiatingProcessFileName in~ ("winword.exe", "excel.exe", "powerpnt.exe", "outlook.exe")
| where FileName in~ ("powershell.exe", "pwsh.exe", "cmd.exe", "wscript.exe", "cscript.exe", "mshta.exe", "rundll32.exe", "regsvr32.exe")
| project TimeGenerated, DeviceName, AccountName, InitiatingProcessFileName, FileName, ProcessCommandLine, InitiatingProcessParentFileName, ProcessId
```
**Triage:** True positive = `WINWORD.EXE` spawning `powershell.exe` with an encoded/remote payload on a finance host. Benign = an Office add-in or template legitimately calling `cmd`/`cscript` for a documented business macro you can attribute.

### H2 · Encoded / obfuscated PowerShell execution — [T1059.001](https://attack.mitre.org/techniques/T1059/001/)
**Hypothesis:** PowerShell is launched with a base64-`EncodedCommand` and/or hidden, non-interactive, execution-policy-bypass flags — a hallmark of fileless droppers and stagers.
```kusto
DeviceProcessEvents
| where ActionType == "ProcessCreated"
| where FileName in~ ("powershell.exe", "pwsh.exe")
| where ProcessCommandLine has_any ("-enc", "-EncodedCommand", "-ec ", " -e ", "FromBase64String", "-w hidden", "-nop", "-noni", "bypass")
| project TimeGenerated, DeviceName, AccountName, InitiatingProcessFileName, ProcessCommandLine, ProcessIntegrityLevel, ProcessId
| sort by TimeGenerated asc
```
**Triage:** True positive = `powershell.exe -nop -w hidden -enc <long base64>` spawned by Office/a LOLBin. Benign = signed management tooling (SCCM, GPO startup scripts) using `-EncodedCommand` from a known service account — confirm the parent and account.

### H3 · LOLBin proxy execution from a script host — [T1218.011](https://attack.mitre.org/techniques/T1218/011/) (rundll32) · [T1218.005](https://attack.mitre.org/techniques/T1218/005/) (mshta)
**Hypothesis:** `rundll32.exe` / `mshta.exe` is launched **by** a script interpreter (PowerShell/cmd) and from a user-writable path or with a URL/`javascript:` argument — proxy execution to evade application controls.
```kusto
DeviceProcessEvents
| where ActionType == "ProcessCreated"
| where FileName in~ ("rundll32.exe", "mshta.exe", "regsvr32.exe")
| where InitiatingProcessFileName in~ ("powershell.exe", "pwsh.exe", "cmd.exe", "wscript.exe", "cscript.exe")
| where ProcessCommandLine has_any (@"\AppData\", @"\Temp\", "http://", "https://", "javascript:", "vbscript:", ".hta")
| project TimeGenerated, DeviceName, AccountName, InitiatingProcessFileName, FileName, ProcessCommandLine, FolderPath, ProcessId
```
**Triage:** True positive = `mshta.exe http://badupdate-cdn.com/...` or `rundll32` loading a DLL from `%APPDATA%`, parented by PowerShell. Benign = a legitimate installer/MSI calling `rundll32` against a system DLL in `System32`.

### H4 · System-utility name running from a non-system path (masquerade / cred dumper) — [T1036.005](https://attack.mitre.org/techniques/T1036/005/)
**Hypothesis:** A process named like a Windows binary (`svchost`, `lsass`, `services`) executes from outside `System32`/`SysWOW64`, optionally with credential-theft arguments — a renamed tool masquerading as a system process.
```kusto
DeviceProcessEvents
| where ActionType == "ProcessCreated"
| where FileName has_any ("svchost", "lsass", "services", "csrss", "winlogon")
| where FolderPath !has @"\Windows\System32" and FolderPath !has @"\Windows\SysWOW64"
| project TimeGenerated, DeviceName, AccountName, FileName, FolderPath, ProcessCommandLine, InitiatingProcessFileName, InitiatingProcessAccountName, ProcessId
```
**Triage:** True positive = `svchost_helper.exe` in `%APPDATA%\WinUpdate` running `sekurlsa::logonpasswords`. Benign = a vendor agent that legitimately ships a `services`-named helper inside `Program Files` (verify signer and path).

## 🔗 Correlates with
- **DeviceFileEvents** on `DeviceId` + `SHA256` (and `FileName`/`FolderPath`) — tie the **execution** of `SecurityUpdate_KB5039211.exe` / `svchost_helper.exe` to its on-disk **drop/rename**; same hashes appear in both samples.
- **DeviceNetworkEvents** on `DeviceId` (+ event time, `InitiatingProcessId`/`InitiatingProcessFileName`) — pivot from the `powershell.exe`/`mshta.exe` process to its outbound C2 connection (`badupdate-cdn.com` / `185.220.101.2`).
- **DeviceEvents** on `DeviceId` (+ `InitiatingProcessId`, time) — see whether an ASR rule or AMSI scan **audited vs blocked** the same encoded-PowerShell / Office-child execution.
- **DeviceLogonEvents** on `DeviceName`/`DeviceId` — anchor the process tree to the RemoteInteractive logon for **alexw** on FIN-WS-07 at ~08:35 that preceded it.

## 📚 References
- DeviceProcessEvents table reference — https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/deviceprocessevents
- Microsoft Defender XDR advanced hunting — `DeviceProcessEvents` schema — https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-deviceprocessevents-table
- Connect Microsoft Defender XDR data to Microsoft Sentinel — https://learn.microsoft.com/en-us/azure/sentinel/connect-microsoft-365-defender
