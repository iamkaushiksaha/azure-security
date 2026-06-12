# DeviceLogonEvents

> **Category:** Security (Microsoft Defender XDR — Defender for Endpoint)
> **Connector / source:** Microsoft Defender XDR connector (advanced hunting `DeviceLogonEvents` table, streamed by the Defender for Endpoint sensor on enrolled devices)
> **Table plan:** Basic supported — the reference flags **Basic log: Yes** (also Auxiliary / lake-only ingestion). Defaults to Analytics unless the workspace explicitly sets the table to Basic.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/devicelogonevents

## What this table is
Each row is a **sign-in or other authentication event observed locally on a device** by the Microsoft Defender for Endpoint sensor. It records who logged on (`AccountName` / `AccountDomain` / `AccountSid`), onto which device (`DeviceName` / `DeviceId`), how (`LogonType` — interactive, remote interactive/RDP, network, batch, service), the result (`ActionType` = `LogonSuccess` / `LogonFailed` / `LogonAttempted`), and where the logon came from (`RemoteIP` / `RemoteDeviceName`). Rows appear continuously as users and processes authenticate to endpoints. In a SOC it is the primary endpoint-side source for **brute-force / password-spray detection, lateral-movement tracking (RDP and network logons between hosts), and surfacing local-admin logons** — complementing Entra `SigninLogs` (cloud) and the Windows `SecurityEvent` 4624/4625 stream.

## Schema
Full column list, validated against the Microsoft Learn reference. Types are KQL/Log Analytics types.

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | Date and time the event was recorded by the MDE agent on the endpoint. |
| ActionType | string | Type of activity that triggered the event — the logon **result** (`LogonSuccess`, `LogonFailed`, `LogonAttempted`). |
| LogonType | string | Type of logon session: interactive, remote interactive (RDP), network, batch, service. |
| AccountName | string | User name of the account that logged on. |
| AccountDomain | string | Domain of the account. |
| AccountSid | string | Security identifier (SID) of the account. |
| DeviceName | string | Fully qualified domain name (FQDN) of the device the logon targeted. |
| DeviceId | string | Unique identifier for the device in the service. |
| FailureReason | string | Information explaining why the recorded action failed (populated on `LogonFailed`). |
| RemoteIP | string | IP address that was being connected from / to. |
| RemoteIPType | string | Type of IP address — Public, Private, Reserved, Loopback, Teredo, FourToSixMapping, Broadcast. |
| RemotePort | int | TCP port on the remote device that was being connected to. |
| RemoteDeviceName | string | Name of the device that performed a remote operation on the affected machine (FQDN, NetBIOS, or host name). |
| Protocol | string | Protocol used during the communication. |
| IsLocalAdmin | bool | Whether the user is a local administrator on the machine. |
| LogonId | long | Identifier for a logon session; unique per machine only between restarts. |
| AppGuardContainerId | string | Identifier for the virtualized Application Guard container isolating browser activity. |
| AdditionalFields | dynamic | Additional information about the entity or event (nested JSON). |
| InitiatingProcessAccountName | string | User name of the account that ran the process responsible for the event. |
| InitiatingProcessAccountDomain | string | Domain of the account that ran the initiating process. |
| InitiatingProcessAccountSid | string | SID of the account that ran the initiating process. |
| InitiatingProcessAccountUpn | string | UPN of the account that ran the initiating process. |
| InitiatingProcessAccountObjectId | string | Azure AD object ID of the account that ran the initiating process. |
| InitiatingProcessFileName | string | Name of the process that initiated the event. |
| InitiatingProcessFolderPath | string | Folder containing the initiating process image file. |
| InitiatingProcessCommandLine | string | Command line used to run the initiating process. |
| InitiatingProcessId | long | Process ID (PID) of the initiating process. |
| InitiatingProcessCreationTime | datetime | When the initiating process was started. |
| InitiatingProcessFileSize | long | Size in bytes of the initiating process image file. |
| InitiatingProcessIntegrityLevel | string | Integrity level of the initiating process. |
| InitiatingProcessTokenElevation | string | UAC privilege-elevation token type applied to the initiating process. |
| InitiatingProcessMD5 | string | MD5 hash of the initiating process image file. |
| InitiatingProcessSHA1 | string | SHA-1 hash of the initiating process image file. |
| InitiatingProcessSHA256 | string | SHA-256 hash of the initiating process image file (usually unpopulated — prefer SHA1). |
| InitiatingProcessParentFileName | string | Name of the parent process that spawned the initiating process. |
| InitiatingProcessParentId | long | PID of the parent process. |
| InitiatingProcessParentCreationTime | datetime | When the parent of the initiating process was started. |
| InitiatingProcessSessionId | long | Windows session ID of the initiating process. |
| InitiatingProcessUniqueId | string | Unique identifier of the initiating process (Process Start Key on Windows). |
| IsInitiatingProcessRemoteSession | bool | Whether the initiating process ran under an RDP session (true) or locally (false). |
| InitiatingProcessRemoteSessionDeviceName | string | Device name of the remote device the initiating process's RDP session came from. |
| InitiatingProcessRemoteSessionIP | string | IP address of the remote device the initiating process's RDP session came from. |
| ReportId | long | Event identifier based on a repeating counter; unique only with DeviceName + event time. |
| MachineGroup | string | Machine group used by role-based access control to determine access to the machine. |
| SourceSystem | string | Type of agent the event was collected by. |
| TenantId | string | The Log Analytics workspace ID. |
| Type | string | The name of the table. |

> Plus **8 standard `InitiatingProcess*VersionInfo*` columns** (`InitiatingProcessVersionInfoCompanyName`, `…FileDescription`, `…InternalFileName`, `…OriginalFileName`, `…ProductName`, `…ProductVersion`) and the billing/system columns `_BilledSize` (real), `_IsBillable` (string). **Total: 54 columns.** No column has been invented; `AdditionalFields` is the only dynamic/nested blob.

## Key columns for detection & hunting
- **Identity:** `AccountName` + `AccountDomain` (+ `AccountSid` as the stable key). The *actor that launched the logon-triggering process* is `InitiatingProcessAccountName` / `InitiatingProcessAccountUpn` — distinct from the account being logged on.
- **Host / device:** `DeviceName` (FQDN) and `DeviceId` (stable GUID). `RemoteDeviceName` is the **source** host of a remote/network logon.
- **Network:** `RemoteIP`, `RemoteIPType`, `RemotePort`, `Protocol`. For RDP-tunnelled initiating processes also `InitiatingProcessRemoteSessionIP` / `InitiatingProcessRemoteSessionDeviceName`.
- **Outcome / result:** `ActionType` — a **string** with values `LogonSuccess`, `LogonFailed`, `LogonAttempted` (there is **no** numeric result code). `FailureReason` carries the reason on failures.
- **Timestamps:** `TimeGenerated` (sensor record time). Process-side timing via `InitiatingProcessCreationTime`.
- **Join keys (to other tables):** `DeviceName` / `DeviceId` (→ other `Device*` tables), `AccountSid` and `AccountName` (→ `SecurityEvent`, `IdentityLogonEvents`), `RemoteIP` (→ network / sign-in tables), `AccountName`→`UserPrincipalName` mapping (→ `SigninLogs`).

## ⚠️ Schema gotchas
- **`ActionType` is the result, and it is a STRING, not an int.** Filter `ActionType == "LogonFailed"`, never a numeric code. The Windows `SecurityEvent` twin uses EventIDs 4624/4625 instead — do not mix the conventions.
- **`LogonType` (the *kind* of logon) vs `ActionType` (the *result*)** are two different columns. A "RemoteInteractive + LogonSuccess" row is a successful RDP logon; people frequently conflate the two.
- **`AccountName` ≠ `InitiatingProcessAccountName`.** The first is who is being authenticated; the second is the process owner that triggered the event (often `SYSTEM`/`System`). Pivot on the right one or your hunt will mis-attribute activity.
- **`RemoteIP` / `RemoteDeviceName` are empty for purely local interactive logons** (e.g. `LogonType == "Interactive"` at the console). Only network / remote-interactive logons populate the source columns — don't treat blanks as "internal".
- **Basic/Auxiliary plan caveat:** this table can be configured as a **Basic** log. Under Basic/Auxiliary plans, scheduled-analytics rules and cross-table `join` behaviour are restricted (KQL-on-query-time limits). Confirm the workspace plan before building alerting on it.

## 🧪 Sample data
[`DeviceLogonEvents_sample.csv`](DeviceLogonEvents_sample.csv) — 23 rows. The rows tell the **Operation Quiet Ledger** endpoint-logon story: a RemoteInteractive (RDP) logon as `alexw` onto **FIN-WS-07** from attacker IP `185.220.101.2` at 08:35, then ~09:00 a **burst of `LogonFailed` network logons against `DC01`** sourced from FIN-WS-07 (account brute force / spray) culminating in a `LogonSuccess` as `itadmin` with `IsLocalAdmin=true` (lateral movement), plus benign interactive/unlock logons by `meganb` on **HR-WS-03**.
The sample uses this curated subset of **real** columns: `TimeGenerated`, `DeviceName`, `DeviceId`, `ActionType`, `LogonType`, `AccountDomain`, `AccountName`, `AccountSid`, `RemoteIP`, `RemoteIPType`, `RemoteDeviceName`, `RemotePort`, `Protocol`, `IsLocalAdmin`, `FailureReason`, `InitiatingProcessFileName`, `InitiatingProcessAccountName`, `ReportId`. This is the **device-logon step (08:35 initial access on FIN-WS-07 → 09:00 lateral movement to DC01)** of the cross-table attack scenario.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · RDP logon from an external/public IP — [T1021.001](https://attack.mitre.org/techniques/T1021/001/)
**Hypothesis:** A successful `RemoteInteractive` (RDP) logon whose `RemoteIP` is Public indicates inbound RDP from outside the corporate estate — a hallmark of initial access on a workstation.
```kusto
DeviceLogonEvents
| where ActionType == "LogonSuccess"
| where LogonType == "RemoteInteractive"
| where RemoteIPType == "Public"
| project TimeGenerated, DeviceName, AccountName, RemoteIP, RemoteDeviceName, Protocol
| sort by TimeGenerated asc
```
**Triage:** True positive = RDP from an unfamiliar public IP (e.g. `185.220.101.2`/`91.219.236.18` on FIN-WS-07). Benign = known admin-jump-host or VPN egress; cross-check the IP against approved RDP sources.

### H2 · Failed-logon burst then success — brute force / password spray — [T1110](https://attack.mitre.org/techniques/T1110/)
**Hypothesis:** Five or more `LogonFailed` events against one device from a single source IP, followed by a `LogonSuccess`, indicates a successful credential-guessing attack (lateral movement to DC01).
```kusto
DeviceLogonEvents
| where LogonType in ("Network", "RemoteInteractive")
| summarize Failures = countif(ActionType == "LogonFailed"),
            Successes = countif(ActionType == "LogonSuccess"),
            DistinctAccounts = dcount(AccountName),
            FirstSeen = min(TimeGenerated), LastSeen = max(TimeGenerated)
        by DeviceName, RemoteIP
| where Failures >= 5 and Successes >= 1
| sort by Failures desc
```
**Triage:** True positive = many failed accounts from one `RemoteIP` against `DC01` ending in a success (here `itadmin`). Benign = a single mistyped-password user; distinct-account fan-out (`DistinctAccounts`) is the spray tell.

### H3 · Successful logon by a local administrator from a remote host — [T1078](https://attack.mitre.org/techniques/T1078/)
**Hypothesis:** A network/remote-interactive `LogonSuccess` where `IsLocalAdmin == true` and a `RemoteIP` is present escalates blast radius — a privileged foothold landing remotely.
```kusto
DeviceLogonEvents
| where ActionType == "LogonSuccess"
| where IsLocalAdmin == true
| where isnotempty(RemoteIP)
| project TimeGenerated, DeviceName, AccountName, LogonType, RemoteIP, RemoteDeviceName, IsLocalAdmin
| sort by TimeGenerated asc
```
**Triage:** True positive = admin logon sourced from a workstation (`FIN-WS-07`) rather than a sanctioned PAW/jump host. Benign = scheduled admin maintenance from a known management subnet.

## 🔗 Correlates with
- **SecurityEvent** on `AccountSid` / `DeviceName` — pivot to Windows 4624/4625 for the full logon package (logon process, auth package, source port) the MDE row summarizes.
- **DeviceProcessEvents / DeviceEvents** on `DeviceId` + time — see what the freshly logged-on session *did* (e.g. 09:00 process creation on FIN-WS-07/DC01).
- **SigninLogs** on `AccountName`→`UserPrincipalName` and `RemoteIP`→`IPAddress` — tie the endpoint logon back to the Entra risky sign-in (08:20 NL) for `alexw`.
- **DeviceNetworkEvents** on `DeviceId` + `RemoteIP` — corroborate the RDP/SMB connection (3389/445) underpinning the remote logon.

## 📚 References
- [DeviceLogonEvents — Azure Monitor reference](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/devicelogonevents)
- [DeviceLogonEvents — Microsoft Defender XDR advanced hunting schema](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-devicelogonevents-table)
