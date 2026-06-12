# DeviceNetworkEvents

> **Category:** Security (Microsoft Defender XDR — Defender for Endpoint / advanced hunting `DeviceNetworkEvents`)
> **Connector / source:** Microsoft Defender for Endpoint (Defender XDR) connector streaming the MDE sensor's `DeviceNetworkEvents` table into the Log Analytics / Sentinel workspace.
> **Table plan:** Basic (the reference flags **Basic log = Yes**; also supports ingestion-time DCR and lake-only ingestion). Frequently kept on Analytics where full KQL / analytic-rule support is required.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/devicenetworkevents

## What this table is
`DeviceNetworkEvents` is the network-connection event stream from Microsoft Defender for Endpoint. Each row is a single network event observed by the MDE sensor on an onboarded endpoint — a connection attempt and its outcome — attributed to the **process that made it**. A row records the local and remote endpoints of the connection (`LocalIP`/`LocalPort`, `RemoteIP`/`RemotePort`), the destination name where known (`RemoteUrl`), the protocol, the address scope (`RemoteIPType`/`LocalIPType` — Public, Private, Loopback, …), and the full initiating-process context (image, command line, account, parent). Rows appear in near-real-time as the sensor reports. In a SOC it is the primary endpoint-side source for **C2 / beaconing detection** (which process on which host repeatedly talked to a rare external host), **exfiltration hunting** (large or unusual outbound from interpreters/LOLBins), and **attribution** — turning a suspicious IP/domain into the exact host, user, and process responsible.

## Schema
Full column list, validated against the Microsoft Learn reference. (Types are the KQL / Log Analytics types: string, int, long, real, datetime, bool, dynamic.)

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | Date and time the event was recorded by the MDE agent on the endpoint. |
| ActionType | string | Type of activity that triggered the event (e.g. `ConnectionSuccess`, `ConnectionFailed`, `ConnectionAttempt`, `InboundConnectionAccepted`, `ListeningConnectionCreated`). |
| DeviceId | string | Unique identifier for the device in the service. |
| DeviceName | string | Fully qualified domain name (FQDN) of the device. |
| LocalIP | string | IP address assigned to the local machine used during communication. |
| LocalIPType | string | Type of the local IP address — `Public`, `Private`, `Reserved`, `Loopback`, `Teredo`, `FourToSixMapping`, `Broadcast`. |
| LocalPort | int | TCP/UDP port on the local machine used during communication. |
| RemoteIP | string | IP address that was being connected to. |
| RemoteIPType | string | Type of the remote IP address — `Public`, `Private`, `Reserved`, `Loopback`, `Teredo`, `FourToSixMapping`, `Broadcast`. |
| RemotePort | int | TCP/UDP port on the remote device that was being connected to. |
| RemoteUrl | string | URL or fully qualified domain name (FQDN) that was being connected to. |
| Protocol | string | IP protocol used — `Tcp` or `Udp`. |
| InitiatingProcessAccountName | string | User name of the account that ran the initiating process. |
| InitiatingProcessAccountDomain | string | Domain of the account that ran the initiating process. |
| InitiatingProcessAccountUpn | string | User principal name (UPN) of the account that ran the initiating process. |
| InitiatingProcessAccountSid | string | Security identifier (SID) of the account that ran the initiating process. |
| InitiatingProcessAccountObjectId | string | Microsoft Entra (Azure AD) object ID of the account that ran the initiating process. |
| InitiatingProcessCommandLine | string | Command line used to run the initiating process. |
| InitiatingProcessCreationTime | datetime | Date and time when the process that initiated the event was started. |
| InitiatingProcessFileName | string | Name of the initiating process. |
| InitiatingProcessFileSize | long | Size (bytes) of the file that ran the process responsible for the event. |
| InitiatingProcessFolderPath | string | Folder containing the initiating process (image file). |
| InitiatingProcessId | long | Process ID (PID) of the initiating process. |
| InitiatingProcessIntegrityLevel | string | Integrity level of the initiating process (e.g. `System`, `High`, `Medium`, `Low`). |
| InitiatingProcessMD5 | string | MD5 hash of the initiating process (image file). |
| InitiatingProcessParentCreationTime | datetime | Date and time when the parent of the responsible process was started. |
| InitiatingProcessParentFileName | string | Name of the parent process that spawned the initiating process. |
| InitiatingProcessParentId | long | Process ID (PID) of the parent process that spawned the initiating process. |
| InitiatingProcessRemoteSessionDeviceName | string | Device name of the remote device from which the initiating process's RDP session was initiated. |
| InitiatingProcessRemoteSessionIP | string | IP address of the remote device from which the initiating process's RDP session was initiated. |
| InitiatingProcessSessionId | long | Windows session ID of the initiating process. |
| InitiatingProcessSHA1 | string | SHA-1 hash of the initiating process (image file). |
| InitiatingProcessSHA256 | string | SHA-256 hash of the initiating process (image file). In some cases this column is not populated — use `InitiatingProcessSHA1` instead. |
| InitiatingProcessTokenElevation | string | Token type indicating presence/absence of UAC privilege elevation applied to the initiating process. |
| InitiatingProcessUniqueId | string | Unique identifier of the initiating process (equals the Process Start Key on Windows devices). |
| InitiatingProcessVersionInfoCompanyName | string | Company name from the initiating process image's version info. |
| InitiatingProcessVersionInfoFileDescription | string | File description from the initiating process image's version info. |
| InitiatingProcessVersionInfoInternalFileName | string | Internal file name from the initiating process image's version info. |
| InitiatingProcessVersionInfoOriginalFileName | string | Original file name from the initiating process image's version info. |
| InitiatingProcessVersionInfoProductName | string | Product name from the initiating process image's version info. |
| InitiatingProcessVersionInfoProductVersion | string | Product version from the initiating process image's version info. |
| IsInitiatingProcessRemoteSession | bool | Whether the initiating process ran under an RDP session (`true`) or locally (`false`). |
| AppGuardContainerId | string | Identifier for the virtualized container used by Application Guard to isolate browser activity. |
| AdditionalFields | dynamic | Additional information about the entity or event (JSON). |
| MachineGroup | string | Machine group of the device (used by RBAC to determine access). |
| ReportId | long | Event identifier based on a repeating counter; unique only in conjunction with `DeviceName`/`DeviceId` and event time. |
| SourceSystem | string | The type of agent the event was collected by (e.g. `OpsManager`, `Linux`, `Azure`). |
| TenantId | string | The Log Analytics workspace ID. |
| Type | string | The name of the table (`DeviceNetworkEvents`). |
| _BilledSize | real | The record size in bytes. |
| _IsBillable | string | Whether ingesting the data is billable (string `true`/`false`). |

> Reference page lists 53 columns. Every detection-relevant column (host, full connection 5-tuple + URL + IP-type, the initiating-process context, IDs/keys, the `AdditionalFields` blob) is listed individually above; the only items not separately broken out are the standard envelope/billing columns, all in the tail of the table.

## Key columns for detection & hunting
- **Identity:** `InitiatingProcessAccountName` / `InitiatingProcessAccountUpn` / `InitiatingProcessAccountSid` / `InitiatingProcessAccountObjectId` — the account that ran the process that made the connection. There is **no separate "target user"**; the only identity on the row is the initiating-process account.
- **Host / device:** `DeviceName` (FQDN) and `DeviceId` (durable service GUID). The connection's *local* host is also `LocalIP`.
- **Network:** the full tuple — `LocalIP`/`LocalPort` (source) and `RemoteIP`/`RemotePort`/`RemoteUrl` (destination), with `Protocol` and the scope flags `RemoteIPType` / `LocalIPType`. For outbound C2/exfil, `RemoteIP` + `RemoteUrl` + `RemotePort` are the workhorses; `RemoteIPType == "Public"` separates external traffic from intranet.
- **Outcome / result:** encoded in **`ActionType`** — `ConnectionSuccess` (completed), `ConnectionFailed` (refused/blocked/unreachable), `ConnectionAttempt`, plus inbound/listening variants (`InboundConnectionAccepted`, `ListeningConnectionCreated`). There is no separate boolean result column.
- **Timestamps:** `TimeGenerated` (agent report time); plus process-time fields `InitiatingProcessCreationTime`, `InitiatingProcessParentCreationTime`.
- **Join keys (to other tables):** `DeviceName` / `DeviceId` (to all `Device*` tables), `RemoteUrl` (to `DnsEvents.Name` / proxy logs / TI domains), `RemoteIP` (to `DnsEvents.IPAddresses`, `StorageBlobLogs.CallerIpAddress`, firewall/NSG flow logs, TI indicators), `InitiatingProcessId` + `DeviceId` (to `DeviceProcessEvents` for the full process tree), `InitiatingProcessAccountUpn` / `InitiatingProcessAccountSid` (to identity tables / `DeviceLogonEvents`).

## ⚠️ Schema gotchas
- **No result/outcome boolean — read `ActionType`.** Success vs failure lives entirely in `ActionType` (`ConnectionSuccess` / `ConnectionFailed` / `ConnectionAttempt`). A `ConnectionFailed` to a bad host still proves intent (the process *tried*); don't filter it out when hunting C2.
- **Direction is in `ActionType`, not a flag.** Most rows are outbound; inbound is `InboundConnectionAccepted` and a local listener is `ListeningConnectionCreated`. For an inbound row the "remote" side is the *peer that connected in* and `RemoteUrl` is typically empty — don't assume Remote == destination of an outbound flow.
- **`RemoteUrl` is best-effort and often empty.** The sensor populates it when it can associate a name (e.g. from the connecting app / SNI), but many rows have only `RemoteIP`. Hunt on `RemoteIP` as the reliable key and treat `RemoteUrl` as enrichment; correlate to `DnsEvents` to recover the name.
- **`LocalPort`/`RemotePort` are `int`, not string** (unlike `StorageBlobLogs`, where the port is glued onto the IP string). And `RemoteIP` here is a **bare IP with no port** — safe to join directly, no `split` needed.
- **Identity is initiating-process-only.** Every account field is prefixed `InitiatingProcess…`; there is no plain `AccountName`/`AccountUpn`. Build the user from `InitiatingProcessAccountUpn` (or SID), not from a non-existent target-account column.
- **`InitiatingProcessSHA256` is often empty** (the doc says so) — prefer `InitiatingProcessSHA1` for the actor-process hash.

## 🧪 Sample data
[`DeviceNetworkEvents_sample.csv`](DeviceNetworkEvents_sample.csv) — 25 rows. Defender for Endpoint network telemetry between ~08:58 and 10:41 on 2026-06-10, telling the **C2 + exfil network step (~09:15–10:20) of "Operation Quiet Ledger"** on **FIN-WS-07** (`alexw`, `LocalIP 10.20.7.31`): `powershell.exe` (parent `rundll32.exe`) makes **repeated, periodic `ConnectionSuccess` to `badupdate-cdn.com` / `91.219.236.18`** on a ~5-minute beacon cadence, a `rundll32.exe` `ConnectionFailed` to the phishing host `login-contoso-sso.com` (`185.220.101.2`), two large outbound flows to `stcontosofin.blob.core.windows.net` (`Get-AzStorageBlob` then `azcopy` upload of `fin_export.7z`), the exfil push to the C2 on port 8080, and an inbound RDP `InboundConnectionAccepted` from the attacker IP — all interleaved with **benign Office 365 / Edge / Teams / SharePoint** connections from `meganb`'s **HR-WS-03** and a nightly `svc-backup` job from **DC01**. This is the network-side corroboration of the FIN-WS-07 process and DNS steps.

The sample uses this curated subset of **real** columns: `TimeGenerated`, `DeviceName`, `DeviceId`, `ActionType`, `LocalIP`, `LocalPort`, `RemoteIP`, `RemoteIPType`, `RemotePort`, `RemoteUrl`, `Protocol`, `InitiatingProcessAccountName`, `InitiatingProcessAccountUpn`, `InitiatingProcessFileName`, `InitiatingProcessCommandLine`, `InitiatingProcessParentFileName`, `InitiatingProcessFolderPath`, `ReportId`.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · Script interpreter / LOLBin connecting to a public IP — [T1071](https://attack.mitre.org/techniques/T1071/)
**Hypothesis:** A script interpreter or proxy-execution binary (`powershell.exe`, `rundll32.exe`, `mshta.exe`, `wscript.exe`, `cscript.exe`) making outbound connections to a **public** remote IP is application-layer C2 — these binaries should rarely talk to the internet directly.
```kusto
DeviceNetworkEvents
| where ActionType in ("ConnectionSuccess", "ConnectionAttempt", "ConnectionFailed")
| where RemoteIPType == "Public"
| where InitiatingProcessFileName in~ ("powershell.exe","rundll32.exe","mshta.exe","wscript.exe","cscript.exe","regsvr32.exe")
| project TimeGenerated, DeviceName, InitiatingProcessAccountUpn, ActionType,
          InitiatingProcessFileName, InitiatingProcessParentFileName,
          RemoteIP, RemotePort, RemoteUrl, InitiatingProcessCommandLine
| sort by TimeGenerated asc
```
**Triage:** True positive = `powershell.exe`/`rundll32.exe` on FIN-WS-07 (`alexw`) reaching `badupdate-cdn.com` / `91.219.236.18`, especially with an `-enc` command line or a `Temp\*.dll` export. Benign = a signed updater or admin script hitting a known Microsoft endpoint (`login.microsoftonline.com`, `*.blob.core.windows.net`).

### H2 · Beaconing to a rare RemoteUrl with regular cadence — [T1071.001](https://attack.mitre.org/techniques/T1071.001/)
**Hypothesis:** A single host making many connections to one rarely-seen external `RemoteUrl` at a near-constant interval is C2 beaconing; low timing jitter is the tell.
```kusto
DeviceNetworkEvents
| where ActionType == "ConnectionSuccess" and RemoteIPType == "Public"
| where isnotempty(RemoteUrl)
| where RemoteUrl !endswith "microsoft.com" and RemoteUrl !endswith "office365.com"
       and RemoteUrl !endswith "windows.net" and RemoteUrl !endswith "live.com"
       and RemoteUrl !endswith "microsoftonline.com" and RemoteUrl !endswith "sharepoint.com"
       and RemoteUrl !endswith "bing.com"
| order by DeviceName, RemoteUrl, TimeGenerated asc
| serialize
| extend GapSec = datetime_diff('second', TimeGenerated, prev(TimeGenerated))
| where prev(DeviceName) == DeviceName and prev(RemoteUrl) == RemoteUrl
| summarize Connections = count(), Hosts = dcount(DeviceName),
            AvgGapSec = avg(GapSec), StdevGapSec = stdev(GapSec),
            FirstSeen = min(TimeGenerated), LastSeen = max(TimeGenerated)
        by DeviceName, RemoteUrl, RemoteIP
| where Connections >= 5 and StdevGapSec < 60
| sort by Connections desc
```
**Triage:** True positive = FIN-WS-07 → `badupdate-cdn.com` (`91.219.236.18`) with many connections and a tight ~300 s gap (low stdev). Benign = a chatty SaaS app or telemetry endpoint — check whether the URL is corporate-known and whether the initiating process is signed.

### H3 · Large / unusual outbound from an interpreter — likely exfil — [T1041](https://attack.mitre.org/techniques/T1041/)
**Hypothesis:** Interpreters or transfer LOLBins (`azcopy.exe`, `powershell.exe`, `rundll32.exe`) opening connections to storage/object endpoints or to the C2 on non-standard high ports indicate staging or exfiltration of collected data.
```kusto
DeviceNetworkEvents
| where ActionType == "ConnectionSuccess" and RemoteIPType == "Public"
| where InitiatingProcessFileName in~ ("azcopy.exe","powershell.exe","rundll32.exe","curl.exe","bitsadmin.exe")
| where RemoteUrl has_any ("blob.core.windows.net","badupdate-cdn.com") or RemotePort in (8080, 8443, 8888)
| project TimeGenerated, DeviceName, InitiatingProcessAccountUpn,
          InitiatingProcessFileName, InitiatingProcessParentFileName,
          RemoteUrl, RemoteIP, RemotePort, InitiatingProcessCommandLine
| sort by TimeGenerated asc
```
**Triage:** True positive = `azcopy.exe`/`rundll32.exe` on FIN-WS-07 pushing `fin_export.7z` to `stcontosofin.blob.core.windows.net` or to `badupdate-cdn.com:8080`. Benign = an approved backup/sync job (`svc-backup` on DC01 to `login.microsoftonline.com`) — verify the account, host, and that the destination is sanctioned.

### H4 · Inbound connection accepted on a remote-access port from a public IP — [T1133](https://attack.mitre.org/techniques/T1133/)
**Hypothesis:** A workstation accepting an inbound connection (`InboundConnectionAccepted`) on a remote-access port (RDP 3389, SSH 22, WinRM 5985/5986) directly from a **public** peer is unexpected and may be hands-on-keyboard ingress.
```kusto
DeviceNetworkEvents
| where ActionType == "InboundConnectionAccepted"
| where RemoteIPType == "Public"
| where LocalPort in (3389, 22, 5985, 5986)
| project TimeGenerated, DeviceName, LocalIP, LocalPort, RemoteIP, RemotePort,
          InitiatingProcessFileName, InitiatingProcessAccountUpn
| sort by TimeGenerated asc
```
**Triage:** True positive = FIN-WS-07 accepting inbound RDP (`LocalPort 3389`) from `185.220.101.2` (attacker). Benign = inbound from an internal jump host (`RemoteIPType == "Private"`) — public-sourced RDP to a workstation is almost always wrong.

## 🔗 Correlates with
- **DnsEvents** on `RemoteUrl` ↔ `Name` (and `RemoteIP` ↔ `IPAddresses`) — tie the outbound connection to the DNS lookup that resolved `badupdate-cdn.com` for the same host; DNS shows the name was asked for, this table shows the connection completed.
- **DeviceProcessEvents** on `DeviceId` + `InitiatingProcessId` (+ event time) — pivot from the connection to the full process tree (4688-equivalent) that launched the interpreter, recovering the parent chain and original command line.
- **StorageBlobLogs** on `RemoteIP` ↔ `CallerIpAddress` (strip the `:port` on the StorageBlobLogs side) — confirm the outbound to `*.blob.core.windows.net` corresponds to the `ListBlobs`/`GetBlob`/`PutBlob` exfil requests against `stcontosofin`.
- **DeviceLogonEvents** on `DeviceName` + `InitiatingProcessAccountSid` — anchor the network activity to alexw's interactive logon on FIN-WS-07 and the inbound RDP session.
- **SigninLogs** on `InitiatingProcessAccountUpn` ↔ `UserPrincipalName` — connect the endpoint network activity to the 08:20 risky Entra sign-in from the Netherlands.

## 📚 References
- DeviceNetworkEvents table reference — https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/devicenetworkevents
- Microsoft Defender XDR advanced hunting — DeviceNetworkEvents schema — https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-devicenetworkevents-table
- MITRE ATT&CK — Application Layer Protocol (T1071) — https://attack.mitre.org/techniques/T1071/
