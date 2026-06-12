# DeviceEvents

> **Category:** Security (Microsoft Defender XDR — Defender for Endpoint / advanced hunting `DeviceEvents`)
> **Connector / source:** Microsoft Defender for Endpoint (Defender XDR) connector streaming the MDE agent's `DeviceEvents` table into the Log Analytics / Sentinel workspace.
> **Table plan:** Basic (the reference flags **Basic log = Yes**; also supports lake-only ingestion). Frequently kept on Analytics where full KQL/analytics-rule support is required.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/deviceevents

## What this table is
`DeviceEvents` is the catch-all event stream from Microsoft Defender for Endpoint — the "miscellaneous" advanced-hunting table that holds event types not covered by the more specific `Device*` tables (process, network, file, logon, registry, image-load). Each row is a single security-relevant action observed on an onboarded endpoint, keyed by **`ActionType`**: ASR (attack-surface-reduction) rule audits/blocks, AMSI script scans, Exploit Guard / network-protection / SmartScreen blocks, antivirus detections, PnP (USB) device connections, controlled-folder-access events, and assorted credential/persistence telemetry. Rows appear in near-real-time as the MDE sensor reports them. In a SOC it is the primary source for **ASR and AMSI tuning**, **LOLBin and fileless-attack hunting**, and confirming that an endpoint control actually **blocked vs only audited** a malicious action.

## Schema
Full column list, validated against the Microsoft Learn reference. (Types are the KQL/Log Analytics types: string, int, long, real, datetime, bool, dynamic.)

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | Date and time the event was recorded by the MDE agent on the endpoint. |
| ActionType | string | Type of activity that triggered the event — the event's category key (e.g. `AsrOfficeChildProcessBlocked`, `AntivirusDetection`, `PnpDeviceConnected`). |
| DeviceName | string | Fully qualified domain name (FQDN) of the device. |
| DeviceId | string | Unique identifier for the device in the service. |
| AccountName | string | User name of the account the action applied to. |
| AccountDomain | string | Domain of the account. |
| AccountSid | string | Security identifier (SID) of the account. |
| AdditionalFields | dynamic | Additional information about the entity or event (JSON; the per-`ActionType` payload — rule IDs, threat names, scan results, USB descriptors, etc.). |
| AppGuardContainerId | string | Identifier for the virtualized container used by Application Guard to isolate browser activity. |
| FileName | string | Name of the file that the recorded action was applied to. |
| FolderPath | string | Folder path of the file the recorded action was applied to. |
| FileSize | long | Size of the file in bytes. |
| FileOriginIP | string | IP address where the file was downloaded from. |
| FileOriginUrl | string | URL where the file was downloaded from. |
| MD5 | string | MD5 hash of the file that the recorded action was applied to. |
| SHA1 | string | SHA-1 hash of the file that the recorded action was applied to. |
| SHA256 | string | SHA-256 of the file that the recorded action was applied to. |
| ProcessCommandLine | string | Command line used to create the new process. |
| ProcessCreationTime | datetime | Date and time the process was created. |
| ProcessId | long | Process ID (PID) of the newly created process. |
| ProcessTokenElevation | string | Token type indicating presence/absence of UAC privilege elevation applied to the newly created process. |
| CreatedProcessSessionId | long | Windows session ID of the created process. |
| IsProcessRemoteSession | bool | Whether the created process ran under an RDP session (true) or locally (false). |
| ProcessRemoteSessionDeviceName | string | Device name of the remote device from which the created process's RDP session was initiated. |
| ProcessRemoteSessionIP | string | IP address of the remote device from which the created process's RDP session was initiated. |
| InitiatingProcessAccountName | string | User name of the account that ran the process responsible for the event. |
| InitiatingProcessAccountDomain | string | Domain of the account that ran the process responsible for the event. |
| InitiatingProcessAccountUpn | string | User principal name (UPN) of the account that ran the process responsible for the event. |
| InitiatingProcessAccountSid | string | Security identifier (SID) of the account that ran the process responsible for the event. |
| InitiatingProcessAccountObjectId | string | Azure AD object ID of the user account that ran the process responsible for the event. |
| InitiatingProcessCommandLine | string | Command line used to run the process that initiated the event. |
| InitiatingProcessCreationTime | datetime | Date and time when the process that initiated the event was started. |
| InitiatingProcessFileName | string | Name of the process that initiated the event. |
| InitiatingProcessFolderPath | string | Folder containing the process (image file) that initiated the event. |
| InitiatingProcessFileSize | long | Size in bytes of the file that ran the process responsible for the event. |
| InitiatingProcessId | long | Process ID (PID) of the process that initiated the event. |
| InitiatingProcessParentFileName | string | Name of the parent process that spawned the process responsible for the event. |
| InitiatingProcessParentId | long | Process ID (PID) of the parent process that spawned the process responsible for the event. |
| InitiatingProcessParentCreationTime | datetime | Date and time when the parent of the responsible process was started. |
| InitiatingProcessLogonId | long | Identifier for a logon session of the initiating process (unique per machine between restarts). |
| InitiatingProcessSessionId | long | Windows session ID of the initiating process. |
| InitiatingProcessMD5 | string | MD5 hash of the process (image file) that initiated the event. |
| InitiatingProcessSHA1 | string | SHA-1 hash of the process (image file) that initiated the event. |
| InitiatingProcessSHA256 | string | SHA-256 hash of the initiating process (usually not populated — prefer SHA1). |
| InitiatingProcessUniqueId | string | Unique identifier of the initiating process (equals the Process Start Key on Windows). |
| IsInitiatingProcessRemoteSession | bool | Whether the initiating process ran under an RDP session (true) or locally (false). |
| InitiatingProcessRemoteSessionDeviceName | string | Device name of the remote device from which the initiating process's RDP session was initiated. |
| InitiatingProcessRemoteSessionIP | string | IP address of the remote device from which the initiating process's RDP session was initiated. |
| InitiatingProcessVersionInfoCompanyName | string | Company name from the initiating process image's version info. |
| InitiatingProcessVersionInfoProductName | string | Product name from the initiating process image's version info. |
| InitiatingProcessVersionInfoProductVersion | string | Product version from the initiating process image's version info. |
| InitiatingProcessVersionInfoInternalFileName | string | Internal file name from the initiating process image's version info. |
| InitiatingProcessVersionInfoOriginalFileName | string | Original file name from the initiating process image's version info. |
| InitiatingProcessVersionInfoFileDescription | string | File description from the initiating process image's version info. |
| LogonId | long | Identifier for a logon session (unique per machine between restarts). |
| LocalIP | string | IP address assigned to the local machine during communication. |
| LocalPort | int | TCP port on the local machine used during communication. |
| RemoteIP | string | IP address that was being connected to. |
| RemotePort | int | TCP port on the remote device that was being connected to. |
| RemoteUrl | string | URL or fully qualified domain name (FQDN) that was being connected to. |
| RemoteDeviceName | string | Name of the device that performed a remote operation on the affected machine (FQDN, NetBIOS, or host name). |
| RegistryKey | string | Registry key the recorded action was applied to. |
| RegistryValueName | string | Name of the registry value the recorded action was applied to. |
| RegistryValueData | string | Data of the registry value the recorded action was applied to. |
| MachineGroup | string | Machine group of the device (used by RBAC to determine access). |
| ReportId | long | Event identifier based on a repeating counter; unique only in conjunction with DeviceName/`DeviceId` and event time. |
| SourceSystem | string | The type of agent the event was collected by (e.g. `OpsManager`, `Linux`, `Azure`). |
| TenantId | string | The Log Analytics workspace ID. |
| Type | string | The name of the table (`DeviceEvents`). |
| _BilledSize | real | The record size in bytes. |
| _IsBillable | string | Whether ingesting the data is billable (string `true`/`false`). |

> Full reference table is 73 columns. Every detection-relevant column (identities, hashes, file/registry, initiating-process context, network, IDs/keys, the `AdditionalFields` blob) is listed individually above; the only items not separately broken out are the standard envelope/billing columns, all of which appear in the tail of the table.

## Key columns for detection & hunting
- **Identity:** `AccountName` + `AccountDomain` + `AccountSid` (the account the action applied to), and `InitiatingProcessAccountName` / `InitiatingProcessAccountUpn` / `InitiatingProcessAccountSid` for the account that launched the responsible process. UPN is only reliably present on the initiating-process side (`InitiatingProcessAccountUpn`).
- **Host / device:** `DeviceName` (FQDN) and `DeviceId` (durable service GUID). `RemoteDeviceName` for cross-host actions (e.g. WMI/PsExec onto another machine).
- **Network:** `RemoteIP` / `RemotePort` / `RemoteUrl` and `LocalIP` / `LocalPort`; download provenance in `FileOriginIP` / `FileOriginUrl`. Many event types instead carry the IP/URL inside `AdditionalFields`.
- **Outcome / result:** there is no single result column — outcome is encoded in **`ActionType`** itself (`…Audited` vs `…Blocked`), with detail (e.g. `IsAudit`, `WasRemediated`, `Decision`, `ScanResult`) inside the dynamic `AdditionalFields`.
- **Timestamps:** `TimeGenerated` (agent report time); plus process-time fields `ProcessCreationTime`, `InitiatingProcessCreationTime`, `InitiatingProcessParentCreationTime`.
- **Join keys (to other tables):** `DeviceName` / `DeviceId` (to all `Device*` tables), `InitiatingProcessAccountUpn` / `AccountSid` (to identity tables), `SHA1` / `SHA256` / `MD5` (file reputation pivots), `RemoteIP` / `RemoteUrl` (to network tables), `ReportId` (+ DeviceName + event time for exact dedupe).

## ⚠️ Schema gotchas
- **No result/outcome column.** Success-vs-block lives in the `ActionType` suffix (`Audited` / `Blocked`) and in `AdditionalFields` — never assume an event was prevented; an `…Audited` ASR event means the action *ran*. Filter audit-only rules separately from enforced ones.
- **`AdditionalFields` is dynamic JSON** and is the only place much of the per-event context exists (rule IDs/names, threat names, USB descriptors, scan verdicts, sometimes RemoteIP). You must `parse_json()` / `todynamic()` and index it — its keys vary by `ActionType`.
- **UPN is asymmetric.** `AccountName`/`AccountSid` are populated for the target account but there is no `AccountUpn`; only `InitiatingProcessAccountUpn` exists. Build user identity from SID or from the initiating-process UPN, not from a target UPN.
- **`SHA256` is usually empty** (the doc says so) — prefer `SHA1` for the affected file and `InitiatingProcessSHA1` for the actor process.
- **`ReportId` is not globally unique** — it is a repeating counter; dedupe with `DeviceName`/`DeviceId` + event time, not `ReportId` alone.
- **Several MS Learn column descriptions are copy-paste wrong** (`FileName`, `FolderPath` are described as "Domain of the account"). Trust the column *name*, not that stray description.

## 🧪 Sample data
[`DeviceEvents_sample.csv`](DeviceEvents_sample.csv) — 24 rows. Defender for Endpoint telemetry for FIN-WS-07 between ~08:31 and 09:15 on 2026-06-10: a malicious `.docm` trips the Office-child-process ASR rule (audit then block), an encoded PowerShell downloader is caught by AMSI, mshta/rundll32 LOLBins drop a beacon, LSASS-dump and persistence (scheduled task, service, admin-group add) attempts are blocked or detected, and an outbound C2 connection to `badupdate-cdn.com` (185.220.101.2) is firewalled — interleaved with benign HR-WS-03 noise (USB insert, controlled-folder audit, SmartScreen, clean AV scan). This is the **endpoint-control slice (~08:35–09:15) of "Operation Quiet Ledger"** — it corroborates the FIN-WS-07 device-logon and process-creation steps with what MDE's defenses observed and which actions were stopped vs only audited.

The sample uses this curated subset of **real** columns: `TimeGenerated`, `DeviceName`, `DeviceId`, `ActionType`, `FileName`, `FolderPath`, `SHA1`, `AccountName`, `AccountDomain`, `AccountSid`, `InitiatingProcessAccountName`, `InitiatingProcessAccountUpn`, `InitiatingProcessFileName`, `InitiatingProcessCommandLine`, `InitiatingProcessParentFileName`, `RemoteUrl`, `AdditionalFields`, `ReportId`.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · ASR rule blocked an attack, not just audited — [T1059](https://attack.mitre.org/techniques/T1059/)
**Hypothesis:** An enforced ASR rule firing on a finance workstation indicates a real malicious action that reached the host (Office spawning a shell, LSASS theft, PSExec/WMI child).
```kusto
DeviceEvents
| where ActionType startswith "Asr"
| extend Fields = parse_json(AdditionalFields)
| extend RuleName = tostring(Fields.RuleName), IsAudit = tobool(Fields.IsAudit)
| where ActionType endswith "Blocked" or IsAudit == false
| project TimeGenerated, DeviceName, AccountName, ActionType, RuleName,
          InitiatingProcessFileName, InitiatingProcessCommandLine
| sort by TimeGenerated asc
```
**Triage:** True positive = an `…Blocked` rule (Office→cmd, lsass credential theft, PSExec/WMI) on FIN-WS-07/DC01 under `alexw`. Benign = an `…Audited` event from an allow-listed backup/admin tool.

### H2 · AMSI caught an encoded / fileless script — [T1059.001](https://attack.mitre.org/techniques/T1059.001/)
**Hypothesis:** AMSI or AV detecting content launched by an encoded (`-enc`) or download-cradle PowerShell command line points to a fileless first stage.
```kusto
DeviceEvents
| where ActionType in ("AntivirusDetection", "AmsiUacScanResult", "AmsiScanResult", "PowerShellCommand")
| where InitiatingProcessCommandLine has_any ("-enc", "-encodedcommand", "DownloadString", "IEX", "IWR")
| extend Fields = parse_json(AdditionalFields)
| project TimeGenerated, DeviceName, AccountName, ActionType,
          ThreatName = tostring(Fields.ThreatName), DetectionSource = tostring(Fields.DetectionSource),
          InitiatingProcessFileName, InitiatingProcessCommandLine
| sort by TimeGenerated asc
```
**Triage:** True positive = AMSI/AV `Detected` on an encoded PowerShell cradle reaching `badupdate-cdn.com`. Benign = admin automation using `-enc` that AV did not flag.

### H3 · LOLBin execution chain (mshta → rundll32) — [T1218](https://attack.mitre.org/techniques/T1218/)
**Hypothesis:** Living-off-the-land binaries (`mshta.exe`, `rundll32.exe`) running attacker content, especially chained as parent→child, indicate proxy execution of a payload.
```kusto
DeviceEvents
| where InitiatingProcessFileName in~ ("mshta.exe", "rundll32.exe", "wmic.exe")
    or InitiatingProcessParentFileName in~ ("mshta.exe", "rundll32.exe")
| project TimeGenerated, DeviceName, AccountName, ActionType,
          InitiatingProcessFileName, InitiatingProcessParentFileName, InitiatingProcessCommandLine
| sort by TimeGenerated asc
```
**Triage:** True positive = `mshta.exe`/`rundll32.exe` loading a `.dll` or `.hta` from a user `Temp` path and chaining into beacon/LSASS activity. Benign = signed `rundll32` invoked by a Microsoft installer.

### H4 · USB / removable-media connection — [T1091](https://attack.mitre.org/techniques/T1091/)
**Hypothesis:** A removable drive plugged into a workstation during an active incident may be an exfil/ingress vector and warrants correlation with the user's other activity.
```kusto
DeviceEvents
| where ActionType == "PnpDeviceConnected"
| extend Fields = parse_json(AdditionalFields)
| project TimeGenerated, DeviceName, AccountName,
          DeviceDescription = tostring(Fields.DeviceDescription),
          ClassName = tostring(Fields.ClassName), UsbDeviceId = tostring(Fields.DeviceId)
| sort by TimeGenerated asc
```
**Triage:** True positive = a USB mass-storage device on FIN-WS-07 under `alexw` during the 08:35–09:15 window. Benign = a known peripheral on HR-WS-03 under routine use.

## 🔗 Correlates with
- **DeviceProcessEvents** on `DeviceId` / `DeviceName` (+ `InitiatingProcessId`, event time) — pivot from a blocked ASR/AMSI event to the full process tree (4688-equivalent) that produced it.
- **DeviceNetworkEvents** on `DeviceName` + `RemoteIP` / `RemoteUrl` — confirm whether the beacon's outbound C2 to `badupdate-cdn.com` / `185.220.101.2` actually completed before Firewall/Network-Protection blocked it.
- **DeviceLogonEvents** on `DeviceName` + `AccountSid` — tie the endpoint-control events back to alexw's 08:35 interactive logon on FIN-WS-07.
- **SigninLogs** on `InitiatingProcessAccountUpn` ↔ `UserPrincipalName` — link local-device activity to the 08:20 risky Entra sign-in from the Netherlands.

## 📚 References
- DeviceEvents table reference — https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/deviceevents
- Attack surface reduction (ASR) rules reference (rule IDs/names) — https://learn.microsoft.com/en-us/defender-endpoint/attack-surface-reduction-rules-reference
- Microsoft Defender XDR advanced hunting — DeviceEvents schema — https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-deviceevents-table
