# DeviceFileEvents

> **Category:** Microsoft Defender XDR (Microsoft Defender for Endpoint) — Security
> **Connector / source:** Microsoft Defender for Endpoint (MDE) advanced hunting, streamed to Microsoft Sentinel via the *Microsoft Defender XDR* connector. Rows are produced by the MDE sensor on each onboarded endpoint.
> **Table plan:** Basic supported (the page flags **Basic log: Yes**); commonly ingested as Analytics for full KQL + analytics-rule support.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/devicefileevents

## What this table is
Each row is a single file-system event observed on a Defender for Endpoint–onboarded device: a file being created, modified, renamed, or deleted. The MDE sensor emits the event together with the file's identity (name, path, hashes), the size, any web download provenance, and — critically — the **initiating process** that performed the action (image name, command line, and the account it ran as). In a SOC this is the workhorse table for tracking malware drops to `%TEMP%`/`%APPDATA%`, tool transfers, credential-dumper artifacts, and the staging of archives prior to exfiltration. It pairs naturally with `DeviceProcessEvents` (the process that wrote the file) and `DeviceNetworkEvents` (the connection that fetched it).

## Schema
Full column list, validated against the Microsoft Learn reference. (Types are the KQL/Log Analytics types: string, int, long, real, datetime, bool, dynamic, guid.)

| Column | Type | Description |
|---|---|---|
| ActionType | string | Type of activity that triggered the event (e.g. `FileCreated`, `FileModified`, `FileRenamed`, `FileDeleted`). |
| AdditionalFields | dynamic | Additional information about the entity or event (JSON blob). |
| AppGuardContainerId | string | Identifier for the virtualized container used by Application Guard to isolate browser activity. |
| _BilledSize | real | The record size in bytes. |
| DeviceId | string | Unique identifier for the device in the service. |
| DeviceName | string | Fully qualified domain name (FQDN) of the device. |
| FileName | string | Name of the file that the recorded action was applied to. |
| FileOriginIP | string | IP address where the file was downloaded from. |
| FileOriginReferrerUrl | string | URL of the web page that links to the downloaded file. |
| FileOriginUrl | string | URL where the file was downloaded from. |
| FileSize | long | Size of the file in bytes. |
| FolderPath | string | Folder containing the file that the recorded action was applied to. |
| InitiatingProcessAccountDomain | string | Domain of the account that ran the process responsible for the event. |
| InitiatingProcessAccountName | string | User name of the account that ran the process responsible for the event. |
| InitiatingProcessAccountObjectId | string | Microsoft Entra object ID of the user account that ran the process responsible for the event. |
| InitiatingProcessAccountSid | string | Security Identifier (SID) of the account that ran the process responsible for the event. |
| InitiatingProcessAccountUpn | string | User principal name (UPN) of the account that ran the process responsible for the event. |
| InitiatingProcessCommandLine | string | Command line used to run the process that initiated the event. |
| InitiatingProcessCreationTime | datetime | Date and time when the process that initiated the event was started. |
| InitiatingProcessFileName | string | Name of the process that initiated the event. |
| InitiatingProcessFileSize | long | Size in bytes of the process (image file) that initiated the event. |
| InitiatingProcessFolderPath | string | Folder containing the process (image file) that initiated the event. |
| InitiatingProcessId | long | Process ID (PID) of the process that initiated the event. |
| InitiatingProcessIntegrityLevel | string | Integrity level of the initiating process (e.g. `Low`, `Medium`, `High`, `System`). Influenced by characteristics such as launch from an internet download. |
| InitiatingProcessMD5 | string | MD5 hash of the process (image file) that initiated the event. |
| InitiatingProcessParentCreationTime | datetime | Date and time when the parent of the process responsible for the event was started. |
| InitiatingProcessParentFileName | string | Name of the parent process that spawned the process responsible for the event. |
| InitiatingProcessParentId | long | Process ID (PID) of the parent process that spawned the process responsible for the event. |
| InitiatingProcessRemoteSessionDeviceName | string | Device name of the remote device from which the initiating process's RDP session was initiated. |
| InitiatingProcessRemoteSessionIP | string | IP address of the remote device from which the initiating process's RDP session was initiated. |
| InitiatingProcessSessionId | long | Windows session ID of the initiating process. |
| InitiatingProcessSHA1 | string | SHA-1 hash of the process (image file) that initiated the event. |
| InitiatingProcessSHA256 | string | SHA-256 hash of the initiating process. **Usually not populated — prefer `InitiatingProcessSHA1`.** |
| InitiatingProcessTokenElevation | string | Token type indicating presence/absence of UAC privilege elevation on the initiating process. |
| InitiatingProcessUniqueId | string | Unique identifier of the initiating process; equals the Process Start Key on Windows devices. |
| InitiatingProcessVersionInfoCompanyName | string | Company name from the version information of the initiating process image. |
| InitiatingProcessVersionInfoFileDescription | string | Description from the version information of the initiating process image. |
| InitiatingProcessVersionInfoInternalFileName | string | Internal file name from the version information of the initiating process image. |
| InitiatingProcessVersionInfoOriginalFileName | string | Original file name from the version information of the initiating process image. |
| InitiatingProcessVersionInfoProductName | string | Product name from the version information of the initiating process image. |
| InitiatingProcessVersionInfoProductVersion | string | Product version from the version information of the initiating process image. |
| IsAzureInfoProtectionApplied | bool | Indicates whether the file is encrypted by Azure Information Protection. |
| _IsBillable | string | Specifies whether ingesting the data is billable. When `false`, ingestion isn't billed. |
| IsInitiatingProcessRemoteSession | bool | Whether the initiating process ran under an RDP session (`true`) or locally (`false`). |
| MachineGroup | string | Machine group of the machine, used by RBAC to determine access. |
| MD5 | string | MD5 hash of the file that the recorded action was applied to. |
| PreviousFileName | string | Original name of the file that was renamed as a result of the action. |
| PreviousFolderPath | string | Original folder containing the file before the recorded action was applied. |
| ReportId | long | Event identifier based on a repeating counter. Unique only in conjunction with the device and event time. |
| RequestAccountDomain | string | Domain of the account used to remotely initiate the activity. |
| RequestAccountName | string | User name of the account used to remotely initiate the activity. |
| RequestAccountSid | string | Security Identifier (SID) of the account used to remotely initiate the activity. |
| RequestProtocol | string | Network protocol used to initiate the activity: `Unknown`, `Local`, `SMB`, or `NFS`. |
| RequestSourceIP | string | IPv4/IPv6 address of the remote device that initiated the activity. |
| RequestSourcePort | int | Source port on the remote device that initiated the activity. |
| SensitivityLabel | string | Label applied to content to classify it for information protection. |
| SensitivitySubLabel | string | Sublabel applied to content; grouped under sensitivity labels but treated independently. |
| SHA1 | string | SHA-1 hash of the file that the recorded action was applied to. |
| SHA256 | string | SHA-256 hash of the file that the recorded action was applied to. |
| ShareName | string | Name of the shared folder containing the file. |
| SourceSystem | string | The type of agent the event was collected by (e.g. `OpsManager`, `Linux`, `Azure`). |
| TenantId | string | The Log Analytics workspace ID. |
| TimeGenerated | datetime | Date and time the event was recorded by the MDE agent on the endpoint. |
| Type | string | The name of the table. |

> All 66 columns from the reference page are listed above; none are grouped.

## Key columns for detection & hunting
- **Identity (actor):** `InitiatingProcessAccountName` / `InitiatingProcessAccountUpn` (the user the writing process ran as); `InitiatingProcessAccountSid` for SID joins; `RequestAccountName`/`RequestAccountSid` when the action was driven remotely (SMB/NFS).
- **Host / device:** `DeviceName` (FQDN) and `DeviceId` (stable GUID — prefer for joins; survives renames).
- **Network:** No local socket columns. Web provenance lives in `FileOriginUrl` / `FileOriginIP` / `FileOriginReferrerUrl`; remote-initiated file ops expose `RequestSourceIP` / `RequestSourcePort` / `RequestProtocol`.
- **Outcome / result:** No success/failure column — the event *is* the outcome. Semantics come from `ActionType` (`FileCreated`, `FileModified`, `FileRenamed`, `FileDeleted`, …).
- **Timestamps:** `TimeGenerated` (recorded by the MDE agent). Process-context times: `InitiatingProcessCreationTime`, `InitiatingProcessParentCreationTime`. There is **no** separate `EventTime` column despite the `ReportId` description implying one.
- **Join keys (to other tables):** `DeviceId` / `DeviceName` (to all `Device*` tables), `SHA256` / `SHA1` / `MD5` (file reputation, `DeviceProcessEvents`, `DeviceImageLoadEvents`), `InitiatingProcessId` + `InitiatingProcessCreationTime` (to `DeviceProcessEvents`), `FileOriginIP` (to `DeviceNetworkEvents`), `InitiatingProcessAccountSid` / `InitiatingProcessAccountUpn` (to identity tables).

## ⚠️ Schema gotchas
- **There is no `EventTime` or `ComputerName` column** even though the `ReportId` description references them. Use `TimeGenerated` + `DeviceName`/`DeviceId` + `ReportId` to identify a unique event.
- **`InitiatingProcessSHA256` is usually empty** — Microsoft's own note says to fall back to `InitiatingProcessSHA1`. Don't build detections that key solely on the initiating-process SHA256.
- **There is no `AccountName` column** — the file actor is `InitiatingProcessAccountName` (process owner) or `RequestAccountName` (remote driver). Querying a bare `AccountName` returns nothing.
- **`PreviousFileName` / `PreviousFolderPath` are only populated for `ActionType == "FileRenamed"`** — they're blank for create/modify/delete, so a rename hunt must filter on the action type first.
- **`_IsBillable` is a *string*, not a bool** (values `"true"`/`"false"`); don't compare it to a boolean literal.
- **No socket/port columns for local activity** — `RequestSource*` only fill in when the operation was driven over SMB/NFS from another host. For local drops, web origin (`FileOrigin*`) is the only network context.

## 🧪 Sample data
[`DeviceFileEvents_sample.csv`](DeviceFileEvents_sample.csv) — 26 rows. On **FIN-WS-07** (~08:40–09:30) the compromised user **alexw** has a malicious payload written to `%TEMP%`/`%APPDATA%` after a download from `badupdate-cdn.com`, a renamed credential-dumper dropped as `svchost_helper.exe`, and finance documents staged into a `.zip` archive ahead of exfiltration — interleaved with benign Office temp/autosave files for signal-vs-noise.
The sample uses this curated subset of **real** columns: `TimeGenerated`, `DeviceName`, `DeviceId`, `ActionType`, `FileName`, `FolderPath`, `SHA256`, `SHA1`, `MD5`, `FileSize`, `FileOriginUrl`, `FileOriginIP`, `PreviousFileName`, `PreviousFolderPath`, `InitiatingProcessFileName`, `InitiatingProcessCommandLine`, `InitiatingProcessAccountName`, `InitiatingProcessFolderPath`, `ReportId`. This is the **file-drop / staging** step of *Operation Quiet Ledger* (between the FIN-WS-07 device logon and the blob-exfil stage).

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · Executable dropped to user-writable temp from the web — [T1105](https://attack.mitre.org/techniques/T1105/)
**Hypothesis:** Malware delivery writes a `.exe`/`.dll`/`.scr` into `%TEMP%` or `%APPDATA%` and the file carries a web download origin.
```kusto
DeviceFileEvents
| where ActionType == "FileCreated"
| where FolderPath has_any (@"\AppData\Local\Temp", @"\AppData\Roaming")
| where FileName endswith ".exe" or FileName endswith ".dll" or FileName endswith ".scr"
| where isnotempty(FileOriginUrl)
| project TimeGenerated, DeviceName, FileName, FolderPath, FileOriginUrl, FileOriginIP, SHA256, InitiatingProcessFileName
```
**Triage:** True positive = an unsigned binary from an unfamiliar CDN (e.g. `badupdate-cdn.com`) dropped by a browser/script. Benign = known installer caching to temp from a corporate/CDN domain you can attribute.

### H2 · System-utility name in a non-system path (renamed credential dumper) — [T1036.003](https://attack.mitre.org/techniques/T1036/003/)
**Hypothesis:** A file is renamed to impersonate a Windows system binary (e.g. `svchost`, `lsass`) but lands outside `System32`.
```kusto
DeviceFileEvents
| where ActionType == "FileRenamed"
| where FileName has_any ("svchost", "lsass", "services", "csrss")
| where FolderPath !has @"\Windows\System32" and FolderPath !has @"\Windows\SysWOW64"
| project TimeGenerated, DeviceName, PreviousFileName, PreviousFolderPath, FileName, FolderPath, SHA256, InitiatingProcessAccountName
```
**Triage:** True positive = a download-named file (e.g. `mimi_x64.exe`) renamed to `svchost_helper.exe` in `%APPDATA%`. Benign = legitimate update staging inside `Program Files` / `WinSxS`.

### H3 · Bulk finance documents archived into a single ZIP (collection/staging) — [T1560.001](https://attack.mitre.org/techniques/T1560/001/)
**Hypothesis:** An archive utility creates a `.zip`/`.7z`/`.rar` shortly after touching multiple business documents — classic pre-exfiltration staging.
```kusto
DeviceFileEvents
| where ActionType in ("FileCreated", "FileModified")
| where FileName endswith ".zip" or FileName endswith ".7z" or FileName endswith ".rar"
| where InitiatingProcessFileName in~ ("7z.exe", "winrar.exe", "rar.exe", "powershell.exe", "tar.exe")
| project TimeGenerated, DeviceName, FileName, FolderPath, FileSize, InitiatingProcessFileName, InitiatingProcessCommandLine, InitiatingProcessAccountName
| sort by FileSize desc
```
**Triage:** True positive = a multi-MB archive of finance files built by `7z.exe`/`powershell.exe` in a temp/staging folder. Benign = a user zipping a legitimate report to a known location.

### H4 · Credential-store / SAM artifacts written to disk — [T1003](https://attack.mitre.org/techniques/T1003/)
**Hypothesis:** Files whose names indicate credential material (`*.dmp` of lsass, `NTDS.dit`, `SAM`, `*.kirbi`) are created locally — a sign of credential dumping output.
```kusto
DeviceFileEvents
| where ActionType == "FileCreated"
| where FileName has_any ("lsass", "ntds.dit", ".kirbi", ".ccache") or FileName endswith ".dmp"
| project TimeGenerated, DeviceName, FileName, FolderPath, FileSize, InitiatingProcessFileName, InitiatingProcessCommandLine, InitiatingProcessAccountName
```
**Triage:** True positive = `lsass.dmp` written to `%TEMP%` by a renamed/unsigned tool. Benign = a genuine crash dump under `%LOCALAPPDATA%\CrashDumps` produced by WER.

## 🔗 Correlates with
- **DeviceProcessEvents** on `DeviceId` + `InitiatingProcessId`/`InitiatingProcessCreationTime` — pivot from "who wrote the file" to the full process tree and parent that launched it.
- **DeviceNetworkEvents** on `DeviceId` + `FileOriginIP` — confirm the download connection (to `badupdate-cdn.com` / `185.220.101.2`) that preceded the drop.
- **DeviceLogonEvents** on `DeviceName`/`DeviceId` — tie the file activity back to the interactive logon for **alexw** on FIN-WS-07 at ~08:35.
- **DeviceFileCertificateInfo** / file-reputation on `SHA256`/`SHA1` — check signer and prevalence of the dropped binary across the estate.

## 📚 References
- DeviceFileEvents table reference — https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/devicefileevents
- Microsoft Defender XDR advanced hunting — `DeviceFileEvents` schema — https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-devicefileevents-table
- Connect Microsoft Defender XDR data to Microsoft Sentinel — https://learn.microsoft.com/en-us/azure/sentinel/connect-microsoft-365-defender
