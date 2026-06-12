# SecurityEvent

> **Category:** Security
> **Connector / source:** Windows Security event log forwarded by the **Azure Monitor Agent (AMA)** via the *Windows Security Events via AMA* connector, or the legacy **Log Analytics / MMA agent** (*Security Events* connector). Also populated by Microsoft Defender for Cloud on monitored VMs.
> **Table plan:** Analytics (default). Supports Basic logs / lake-only ingestion and ingestion-time DCR transforms.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/securityevent

## What this table is
Each row is a single **Windows Security event-log record** collected from a monitored Windows host (workstation, member server, or domain controller). The event is identified by its Windows **`EventID`** (e.g. 4624 successful logon, 4625 failed logon, 4688 process creation, 4672 special privileges assigned, 4720 user account created). Rows appear whenever the host's audit policy logs a matching event and the AMA/MMA data-collection rule forwards it to the workspace. In a SOC this is the workhorse table for **authentication monitoring** (logon success/failure, brute force, lateral movement by `LogonType`), **endpoint process auditing** (4688 command-line execution), and **privilege / persistence detection** (special-privilege logons, account and group changes on domain controllers).

## Schema
Full column list, validated against the Microsoft Learn reference. SecurityEvent is a very wide table (~190 columns) because it flattens every field of every audited Windows event. All detection-relevant columns are listed individually; truly event-specific or rarely-queried columns are grouped at the end.

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | Timestamp when the event was generated on the computer (UTC). |
| EventID | int | The Windows event identifier the provider used (4624, 4625, 4688, 4672, 4720, …). |
| Activity | string | Descriptive title of the event (e.g. `4624 - An account was successfully logged on`). |
| Computer | string | Name of the computer on which the event occurred (the host). |
| Account | string | Canonical security context for the user/service, formatted `DOMAIN\user`. |
| AccountType | string | Whether the account is a `User` or `Machine` account. |
| AccountDomain | string | Subject's domain or computer name. |
| AccountName | string | Bare account name (no domain). |
| LogonType | int | The type of logon performed: 2 Interactive, 3 Network, 4 Batch, 5 Service, 7 Unlock, 8 NetworkCleartext, 9 NewCredentials, 10 RemoteInteractive (RDP), 11 CachedInteractive. |
| LogonTypeName | string | Human-readable logon type (Interactive, Network, RemoteInteractive, Unlock, …). |
| LogonProcessName | string | Name of the registered logon process (e.g. `NtLmSsp`, `Kerberos`, `User32`, `Advapi`). |
| LogonGuid | string | GUID correlating this logon with other events sharing the same logon GUID. |
| LogonID | string | Hexadecimal logon identifier correlating recent events with the same logon. |
| AuthenticationPackageName | string | Authentication package used (`Negotiate`, `NTLM`, `Kerberos`). |
| PackageName | string | NTLM-family sub-package name used during logon. |
| IpAddress | string | Network address (IPv4/IPv6) associated with the event — **the source IP for 4624/4625**. |
| IpPort | string | Network (source) port associated with the event. |
| WorkstationName | string | Machine name from which a logon attempt was performed. |
| Workstation | string | Name of the machine used to perform the event. |
| Status | string | Reason a logon failed (e.g. `0xC000006D`). `0x0` on success. |
| SubStatus | string | Additional failure detail (e.g. `0xC000006A` bad password, `0xC0000064` user not found, `0xC0000234` account locked). |
| FailureReason | string | Textual explanation of the `Status` field (e.g. `Unknown user name or bad password`, `Account locked out`). |
| Subject (SubjectAccount / SubjectUserName / SubjectUserSid / SubjectDomainName / SubjectLogonId) | string | The security principal that **initiated** the event (the actor). `SubjectUserSid` is the actor SID; `SubjectLogonId` ties back to that actor's logon session. |
| TargetAccount | string | The account **targeted** by the event, `DOMAIN\user` (e.g. the account that logged on, or the account created by 4720). |
| TargetUserName | string | Name of the target user account (the account that logged on / was created / ran the new process). |
| TargetUserSid / TargetSid | string | SID associated with the target user or resource. |
| TargetDomainName | string | Domain of the target account. |
| TargetLogonId | string | Logon-session identifier of the target logon (join key across 4624/4634/4688). |
| TargetLinkedLogonId | string | Linked logon id — pairs a filtered (non-elevated) token with its elevated counterpart (UAC). |
| ElevatedToken | string | `Yes`/`No` — whether the logon session is elevated (administrator). |
| TokenElevationType | string | Token type assigned under UAC (`%%1936` full, `%%1937` limited, `%%1938` default). |
| ImpersonationLevel | string | Impersonation level of the logon (e.g. `%%1833` Impersonation). |
| RestrictedAdminMode | string | RemoteInteractive only — `Yes`/`No` whether Restricted Admin mode was used (RDP). |
| VirtualAccount | string | `Yes`/`No` — whether the logon used a virtual account. |
| NewProcessId | string | Hex PID of the new process (4688). |
| NewProcessName | string | Full path + name of the new process executable (4688) — **the spawned binary**. |
| ProcessId | string | Hex PID that generated the event. |
| ProcessName | string | Full path + name of the executable for the process. |
| ParentProcessName | string | Name of the parent process (4688) — the spawning binary. |
| CommandLine | string | Command-line arguments passed to the process (4688; requires command-line auditing). |
| MandatoryLabel | string | Integrity label SID assigned to the new process (e.g. `S-1-16-12288` System, `S-1-16-8192` Medium). |
| CallerProcessName | string | Full path + name of the executable for the process that attempted the logon. |
| CallerProcessId | string | Hex PID of the process that attempted the logon. |
| PrivilegeList | string | Privileges granted/used (4672/4673), e.g. `SeDebugPrivilege`, `SeTcbPrivilege`, `SeBackupPrivilege`. |
| MemberName | string | DN of the account added/removed from a group (4728/4732/4756). |
| MemberSid | string | SID of the account added/removed from a group. |
| UserAccountControl | string | List of changes to the `userAccountControl` attribute (account create/modify). |
| OldUacValue / NewUacValue | string | Previous / new `userAccountControl` flag values. |
| SamAccountName | string | Pre-Windows-2000 logon name for the account. |
| DisplayName | string | Address-book display name for the account. |
| SidHistory | string | Previous SIDs if the object was migrated between domains. |
| PasswordLastSet | string | Last time the account password was changed. |
| ObjectName | string | Name/identifying path of the object access was requested for (4663/4656/4660). |
| ObjectType | string | Type of object accessed (File, Key, SAM_USER, …). |
| ObjectServer | string | Windows subsystem calling the routine (e.g. `Security`). |
| AccessMask | string | Hexadecimal mask of the requested/performed operation. |
| AccessList | string | The specific access rights requested/used. |
| ShareName | string | Name of the accessed network share, `\\*\SHARE`. |
| ShareLocalPath | string | Local path of the accessed network share. |
| RelativeTargetName | string | Target file/folder relative to the network share (5140/5145). |
| ServiceName | string | Name of an installed service (4697) or targeted service. |
| ServiceFileName | string | Image path of the installed service. |
| ServiceType | string | Type of service registered with the Service Control Manager. |
| ServiceStartType | int | How the service is configured to start. |
| Correlation | string | Activity identifiers consumers can use to group related events together. |
| Channel | string | Channel the event was logged to (e.g. `Security`). |
| Task | int | The task defined in the event. |
| Level | string | Severity level (Information, Warning, Error, …). |
| Keywords | string | Bitmask of event keywords (e.g. audit success/failure). |
| EventRecordId | string | Record number assigned to the event when logged. |
| EventSourceName | string | Name of the software that logged the event. |
| EventData | string | Raw event-specific data blob (XML/structured). |
| Process | string | Name of the process that generates the event. |
| SourceComputerId | string | Unique identifier assigned to the source computer. |
| SourceSystem | string | Type of agent that collected the event (`OpsManager` for Windows agent). |
| ManagementGroupName | string | Additional info based on resource type. |
| TenantId | string | Log Analytics workspace ID. |
| Type | string | The name of the table (`SecurityEvent`). |
| _ResourceId | string | Azure resource ID the record is associated with. |
| _SubscriptionId | string | Subscription ID the record is associated with. |
| _BilledSize | real | Record size in bytes. |
| _IsBillable | string | Whether ingesting the record is billable. |

> Plus ~110 additional event-specific standard columns covering Kerberos/TGT fields (`ClientAddress`, `TransmittedServices`, `TargetOutboundUserName`), certificate/CA fields (`CACertificateHash`, `CertificateDatabaseHash`, `TemplateOID`), RADIUS/NPS fields (`NASIdentifier`, `NASIPv4Address`, `EAPType`, `NetworkPolicyName`), device-install fields (`ClassId`, `HardwareIds`, `CompatibleIds`), registry-change fields (`OldValue`, `NewValue`, `ObjectValueName`), domain/account-policy fields (`LockoutThreshold`, `MinPasswordLength`, `MaxPasswordAge`, `MachineAccountQuota`), and trust fields (`DomainSid`, `DomainName`). These are empty unless the matching event type is logged. None are inventible — see the Microsoft Learn page for the complete enumeration.

## Key columns for detection & hunting
- **Identity:** `Account` (canonical `DOMAIN\user`). For the **actor** that initiated the event use `SubjectUserName` / `SubjectAccount` (+ `SubjectUserSid`); for the **target** (who logged on, was created, or ran the process) use `TargetUserName` / `TargetAccount` (+ `TargetUserSid`).
- **Host / device:** `Computer` (the machine the event was collected from). `WorkstationName` / `Workstation` give the originating machine name on logon events.
- **Network:** `IpAddress` + `IpPort` carry the source IP/port for 4624/4625 (**not** `SourceIP`). `ClientAddress` / `RemoteIpAddress` appear on Kerberos/TGT and remote-connection events.
- **Outcome / result:** Use `EventID` itself — **4624 = success, 4625 = failure**. On failures, `Status` / `SubStatus` are hex codes (strings) and `FailureReason` is the human-readable explanation. `Status` is `0x0` on success.
- **Timestamps:** `TimeGenerated` (UTC). There is no separate event-time column; `EventRecordId` orders events within a host.
- **Join keys (to other tables / within table):** `Computer` (↔ `DeviceLogonEvents.DeviceName`, `Heartbeat.Computer`), `IpAddress` (↔ SigninLogs `IPAddress`, network logs), `TargetLogonId` / `SubjectLogonId` / `LogonGuid` (correlate 4624↔4634↔4688↔4672 within the host), `TargetUserSid` / `SubjectUserSid` (SID-based identity correlation), `Correlation`.

## ⚠️ Schema gotchas
- **Source IP is `IpAddress`, not `SourceIP`.** A very common mistake — `SourceIP` does not exist on this table. Sibling Defender tables (`DeviceLogonEvents`) call it `RemoteIP`, so cross-table queries must alias.
- **`Status` / `SubStatus` / `LogonID` / `ProcessId` / `NewProcessId` are STRINGS holding hex** (e.g. `"0xC000006A"`, `"0x3e7"`), not ints. Compare as strings; don't `toint()` them.
- **`EventID` is the outcome signal.** There is no boolean success column — you distinguish success vs failure by `EventID` (4624 vs 4625), and on failures by the `SubStatus` code.
- **`LogonType` is an `int`** (3 = network, 10 = RDP). Don't quote it. The friendly string lives in `LogonTypeName`.
- **The correlation column is `Correlation`** — there is no `CorrelationId` here (differs from SigninLogs/AzureActivity which use `CorrelationId`).
- **`Account` is `DOMAIN\user`**, so a single backslash in CSV/strings. Splitting on `\` requires escaping in KQL (`split(Account, @'\')`).
- **`CommandLine` is empty unless command-line process auditing** (Audit Process Creation + the `ProcessCreationIncludeCmdLine_Enabled` policy) is turned on. Absence is not evidence of a clean process.

## 🧪 Sample data
[`SecurityEvent_sample.csv`](SecurityEvent_sample.csv) — 30 rows. The rows tell the **FIN-WS-07 + DC01 ~09:00 morning** of *Operation Quiet Ledger*: a password-spray burst of 4625 failures against `alexw` from the attacker IP, a successful 4624 (LogonType 3 then RDP 10), a 4672 special-privileges logon, suspicious 4688 process creations (`powershell.exe -enc …`, `rundll32.exe`) spawned from Office, and a 4720 account-created-on-DC01 persistence event — interleaved with benign 4624 interactive logons by `meganb` and routine activity.
The sample uses this curated subset of **real** columns: `TimeGenerated`, `EventID`, `Activity`, `Computer`, `Account`, `TargetAccount`, `TargetUserName`, `SubjectUserName`, `LogonType`, `IpAddress`, `Status`, `SubStatus`, `NewProcessName`, `ParentProcessName`, `CommandLine`, `PrivilegeList`, `TargetUserSid`, `Correlation`. This is the **endpoint authentication + process step (08:35–09:40)** of the cross-table attack scenario; pivot on `Computer` and `IpAddress` into SigninLogs/DeviceLogonEvents.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · Password spray then success — [T1110.003](https://attack.mitre.org/techniques/T1110/003/)
**Hypothesis:** A burst of 4625 failures against one account from a single external IP, immediately followed by a 4624 success from that same IP, indicates a successful spray/guess.
```kusto
SecurityEvent
| where EventID in (4624, 4625)
| where IpAddress == "185.220.101.2"
| summarize Failures = countif(EventID == 4625),
            Successes = countif(EventID == 4624),
            FirstFail = minif(TimeGenerated, EventID == 4625),
            Success   = minif(TimeGenerated, EventID == 4624)
          by Account, IpAddress, Computer
| where Failures >= 3 and Successes >= 1
```
**Triage:** True positive = many failures (bad-password `SubStatus 0xC000006A`) then a success from an external/Tor IP. Benign = a user fat-fingering a password from a known corporate egress IP.

### H2 · Suspicious process from Office / encoded PowerShell — [T1059.001](https://attack.mitre.org/techniques/T1059/001/)
**Hypothesis:** `powershell.exe -enc` or `rundll32.exe` spawned by an Office application is a hallmark of phishing-borne execution.
```kusto
SecurityEvent
| where EventID == 4688
| where (NewProcessName has "powershell.exe" and CommandLine has_any ("-enc", "-EncodedCommand", "-w hidden"))
     or (NewProcessName endswith "rundll32.exe" and ParentProcessName has_any ("WINWORD.EXE", "EXCEL.EXE", "OUTLOOK.EXE"))
| project TimeGenerated, Computer, Account, ParentProcessName, NewProcessName, CommandLine
| sort by TimeGenerated asc
```
**Triage:** True positive = base64/hidden PowerShell or `rundll32` with no DLL args, parented by Office. Benign = IT scripts run by `itadmin` from a console (LogonType 2) with readable arguments.

### H3 · Account created on a domain controller — [T1136.001](https://attack.mitre.org/techniques/T1136/001/)
**Hypothesis:** A 4720 (user account created) on `DC01` outside change windows, especially initiated by a non-admin/compromised actor, signals persistence.
```kusto
SecurityEvent
| where EventID == 4720
| where Computer == "DC01"
| project TimeGenerated, Computer, SubjectUserName, TargetAccount, TargetUserName, TargetUserSid
```
**Triage:** True positive = a new account created by a compromised/atypical `SubjectUserName`. Benign = `itadmin` provisioning during an approved onboarding ticket.

### H4 · Special privileges assigned to a new logon — [T1078](https://attack.mitre.org/techniques/T1078/)
**Hypothesis:** A 4672 granting `SeDebugPrivilege` / `SeTcbPrivilege` to a finance user (not an admin) suggests privileged-account abuse following a lateral move.
```kusto
SecurityEvent
| where EventID == 4672
| where PrivilegeList has_any ("SeDebugPrivilege", "SeTcbPrivilege", "SeBackupPrivilege")
| where Account !has @"CONTOSO\itadmin" and Account !has @"CONTOSO\dvora"
| project TimeGenerated, Computer, Account, TargetUserName, PrivilegeList
```
**Triage:** True positive = sensitive privileges granted to a standard user account (`alexw`) on a workstation. Benign = expected for admin/service accounts and tier-0 hosts.

## 🔗 Correlates with
- **SigninLogs** on `IpAddress` ↔ `IPAddress` — pivot from the on-host 4624/4625 to the matching risky Entra ID sign-in (08:20 NL sign-in) for the same actor IP.
- **DeviceLogonEvents** on `Computer` ↔ `DeviceName` (and `IpAddress` ↔ `RemoteIP`) — corroborate the Windows audit logon with the Defender for Endpoint logon record on FIN-WS-07.
- **Heartbeat** on `Computer` — confirm the host was reporting (or stopped) around the incident window.
- **SecurityAlert** on `Computer` / `Account` — line up Defender/Sentinel alerts that fired on the same host and identity.

## 📚 References
- SecurityEvent table reference — https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/securityevent
- Windows Security Events via AMA connector — https://learn.microsoft.com/en-us/azure/sentinel/data-connectors/windows-security-events-via-ama
- Microsoft Learn: 4688 process-creation auditing / command-line inclusion — https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/component-updates/command-line-process-auditing
