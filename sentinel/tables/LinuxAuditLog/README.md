# LinuxAuditLog

> **Category:** Security
> **Connector / source:** Linux auditd records collected by the **Azure Monitor Agent (AMA)** under **Microsoft Defender for Cloud / Microsoft Sentinel** (the agent ships the kernel audit subsystem's `auditd` event stream into Log Analytics). Legacy collection via the Log Analytics agent (MMA/OMS) populates the same table.
> **Table plan:** Analytics (default). The reference flags **Basic log: No**; ingestion-time DCR transformation **is** supported.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/linuxauditlog

## What this table is
Each row is a single **Linux audit (`auditd`) record** emitted by the kernel audit subsystem on a monitored Linux host and forwarded by AMA. A record has a **`RecordType`** (e.g. `SYSCALL`, `EXECVE`, `PATH`, `USER_AUTH`, `USER_LOGIN`, `USER_CMD`, `CONFIG_CHANGE`, `SERVICE_STOP`) describing what the kernel logged. One logical audit *event* — say, running a command — is usually several rows (a `SYSCALL` plus its `EXECVE`/`PATH`/`CWD`) that all share the same **`SerialNumber`** (the auditd event serial). Rows appear continuously wherever audit rules are loaded — every monitored syscall, authentication, privilege change, and watched-file access. In a SOC this is the primary host-side telemetry for Linux servers: **process-execution / command auditing, SSH authentication (brute-force) analysis, `sudo` / privilege-escalation tracking, and detecting tampering with the audit configuration or watched system files.**

## Schema
Full column list, validated against the Microsoft Learn reference. Types are KQL/Log Analytics types. (The Learn page ships these auditd fields with empty descriptions; descriptions below are the standard Linux Audit System field meanings.)

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | When the record was generated / ingested into Log Analytics. |
| Computer | string | **Host** that produced the audit record (the monitored Linux machine). |
| RecordType | string | The auditd **record type** — `SYSCALL`, `EXECVE`, `PATH`, `CWD`, `USER_AUTH`, `USER_LOGIN`, `USER_ACCT`, `USER_CMD`, `CRED_ACQ`, `CRED_REFR`, `CONFIG_CHANGE`, `SERVICE_START/STOP`, etc. |
| SerialNumber | string | The audit **event serial number**. All records belonging to one logical event share this value (the primary intra-event join key). |
| AuditID | string | Composite audit event identifier (`audit(<epoch.ms>:<serial>)`) — the raw `msg=audit(...)` event key as collected. |
| syscall | string | Name/number of the system call for `SYSCALL` records (e.g. `execve`, `open`, `connect`, `unlink`). |
| exe | string | Full path of the **executable** of the process generating the event (e.g. `/usr/bin/bash`, `/usr/sbin/sshd`). |
| comm | string | The **command** name (the process's `comm`, truncated to 16 chars by the kernel — e.g. `whoami`, `sshd`). |
| exit | string | Exit/return value of the syscall (`0`/`success` or a negative errno string). String, not int. |
| res | string | **Result** of the operation for user-space records — `success` or `failed`. |
| success | string | Whether the syscall/operation succeeded — `yes` or `no`. (Parallel to `res`; string-valued.) |
| result | string | Legacy/alternate result field (kept for older record shapes; usually mirrors `res`). |
| auid | long | **Audit (login) UID** — the original login user, preserved across `su`/`sudo`. `4294967295` (unset, `-1`) for daemon-launched processes. |
| uid | long | Real user ID of the process at the time of the event. |
| euid | long | **Effective** user ID — `0` after a successful privilege escalation (e.g. via `sudo`). |
| egid | long | Effective group ID. |
| gid | long | Real group ID. |
| suid | _(see note)_ | _(Not a separate column on this table — set/audit UIDs beyond the above are carried in `RawRecord`.)_ |
| acct | string | Account name referenced by a user record (e.g. the username an `sshd`/`sudo` auth applies to). |
| user | string | User name associated with the record (where populated). |
| audit_user | string | The login user name resolved from `auid`. |
| effective_user | string | Effective user **name** resolved from `euid`. |
| effective_group | string | Effective group name resolved from `egid`. |
| group | string | Group name resolved from `gid`. |
| uid_field _(see uid)_ | long | — |
| addr | string | **Remote address** for authentication records (the source IP of an SSH/login attempt). |
| hostname | string | Hostname recorded inside the auditd message (as seen by the auth daemon). |
| terminal | string | Terminal associated with the event (e.g. `ssh`, `pts/1`, `cron`). |
| tty | string | TTY the process is attached to (e.g. `pts/0`); empty for non-interactive/daemon processes. |
| ses | long | Audit **session ID** grouping all activity in one login session. |
| pid | long | Process ID. |
| ppid | long | Parent process ID (links a process back to its spawner). |
| comm _(see above)_ | string | — |
| cwd | string | Current working directory at the time of the event (from the `CWD` record). |
| path | string | Filesystem path touched by the event (from `PATH` records — the watched/accessed file). |
| name | string | Object / file name field within a record (e.g. the `name=` of a `PATH` or `CONFIG_CHANGE`). |
| cmd | string | The command/argument string for user-command records (`USER_CMD`, e.g. the encoded `sudo` cmd). |
| key | string | The **audit rule key** (`-k`) that matched — the label given to the firing audit rule (e.g. `recon-exec`, `audit-tamper`). |
| op | string | Operation field — what was done (e.g. `add_rule`, `remove_rule`, `PAM:authentication`). |
| exit _(see above)_ | string | — |
| arch | string | CPU architecture of the syscall record (e.g. `c000003e` for x86-64). |
| argc | long | Argument count for an `EXECVE` record. |
| a0 | string | First raw argument register of the syscall (hex). |
| a1 | string | Second raw syscall argument. |
| a2 | string | Third raw syscall argument. |
| a3 | string | Fourth raw syscall argument. |
| a4 | string | Fifth raw syscall argument. |
| a5 | string | Sixth raw syscall argument. |
| a6 | string | Seventh raw argument (extended records). |
| a7 | string | Eighth raw argument. |
| a8 | string | Ninth raw argument. |
| a9 | string | Tenth raw argument. |
| data | string | Raw data payload field of certain records (e.g. `CONFIG_CHANGE`, `TTY` content). |
| family | string | Address family for socket records (e.g. `inet`, `inet6`, `local`). |
| icmptype | string | ICMP type for network-related audit records. |
| filetype | string | File type of a `PATH` object (`file`, `dir`, `symlink`, …). |
| RawRecord | string | The **complete unparsed auditd message text** — the source of truth when a needed field isn't promoted to its own column. |
| ExternalAgentIp | string | Source IP of the agent/relay that submitted the record (collection-path metadata). |
| vm | string | VM/instance identifier associated with the source host. |
| node | string | Node name as reported in the audit record header. |
| SourceComputerId | guid | Unique identifier (GUID) of the source computer's agent. |
| ComputerEnvironment | string | Environment of the computer — `Azure` or `Non-Azure`. |
| ManagementGroup | string | Operations Manager management group that collected the event (legacy MMA path). |
| ManagementGroupName | string | Name of the management group. |
| TimeUploaded | datetime | When the agent uploaded the record (distinct from `TimeGenerated`). |
| ResourceId | string | Azure resource ID of the source host (Arc/VM). |
| SourceSystem | string | Type of agent that collected the event (e.g. `Linux`). |
| TenantId | string | The Log Analytics workspace ID. |
| Type | string | The name of the table (`LinuxAuditLog`). |

> **Total: 68 columns** on the reference page. Every detection-relevant field above is listed individually (host, record type, identities, result fields, the serial, addresses, paths, audit key). The remaining are standard billing/system columns: `_BilledSize` (real), `_IsBillable` (string), `_ResourceId` (string), `_SubscriptionId` (string). No column has been invented. `RawRecord` is the catch-all raw blob (plain text, **not** JSON); this table has no `dynamic` columns.

## Key columns for detection & hunting
- **Identity:** `auid` (login UID, survives `su`/`sudo` — the *true* actor) and its name `audit_user`; `uid`/`euid` for the real vs **effective** user (a `0` `euid` with non-zero `uid` = privilege gained). For auth records the subject is `acct`. Prefer `auid`/`audit_user` over `uid` when attributing actions to a person.
- **Host / device:** `Computer` (the monitored Linux host). `SourceComputerId` is the stable agent GUID; `node`/`hostname` echo the in-record name.
- **Network:** `addr` is the **source IP** on authentication records (SSH brute force). `family`/`icmptype` describe socket records; raw socket details live in `RawRecord` / the `a*` args.
- **Outcome / result:** `res` (`success`/`failed`), `success` (`yes`/`no`), and `exit` — **all strings**, not ints. For user-auth records read `res`; for syscalls read `success`/`exit`.
- **Timestamps:** `TimeGenerated` (record time) and `TimeUploaded` (agent upload). The raw auditd epoch is inside `AuditID`.
- **Join keys (to other tables):** `SerialNumber` (ties the multiple records of one event together — the key intra-table join); `Computer` (→ `Heartbeat`, `Syslog`, `VMConnection`, Defender `Device*`); `addr`→`IPAddress`/`RemoteIP` (→ `SigninLogs`, `DeviceNetworkEvents`); `acct`/`audit_user`→account name (→ `Syslog`, identity tables).

## ⚠️ Schema gotchas
- **Result columns are STRINGS, not ints.** `res` = `success|failed`, `success` = `yes|no`, `exit` = `0` or an errno string. Filter `where success == "no"` / `res == "failed"`, never a numeric code.
- **`RecordType` is the record kind, not the event.** One user action = several rows (`SYSCALL` + `EXECVE` + `PATH`/`CWD`) sharing one `SerialNumber`. Always `summarize … by SerialNumber` (or join on it) before counting "events", or you will multi-count. `EXECVE` rows carry the command in `comm` but leave `exe`/`syscall` blank — read `exe`/`syscall` from the paired `SYSCALL` row.
- **`auid` vs `uid` vs `euid`.** `auid` is the login identity preserved across `sudo`; `uid` is the current real user; `euid` is effective (becomes `0` on successful escalation). `auid` of **`4294967295`** (`-1`/unset) means a daemon-spawned process with no login user — not user `4294967295`.
- **Field names are lowercase auditd names, not the CamelCase of sibling tables.** It's `exe`, `comm`, `syscall`, `acct`, `addr`, `res` — **not** `ProcessName`/`AccountName`. Friendly names (`ExecutableName`, `EffectiveUser`, `AuditUser`, `CommandName`, `SyscallName`) are documentation aliases that map to `exe` / `effective_user` / `audit_user` / `comm` / `syscall`.
- **Many columns are sparsely populated** — fields are only set when the specific record type carries them (e.g. `addr` only on auth records; `path`/`filetype` only on `PATH`; `cwd` only when a `CWD` record exists). Treat empty as "not applicable to this record type", not as missing data. The authoritative full text is always in `RawRecord`.

## 🧪 Sample data
[`LinuxAuditLog_sample.csv`](LinuxAuditLog_sample.csv) — 42 rows. The rows tell the **Operation Quiet Ledger** Linux-foothold story on **WEB-APP-01** (~08:48–09:30): an **SSH brute force** from attacker IP `185.220.101.2` (a burst of `USER_AUTH res=failed` against root/admin/deploy/webapp) lands a `USER_AUTH res=success` as `webapp`; the actor then runs **recon** (`whoami`/`id`/`uname`), **credential access** (`cat /etc/shadow` → blocked, then `/etc/passwd`), **downloads a payload** (`wget` from `badupdate-cdn.com`), `chmod +x` and **executes `/tmp/payload`** which beacons to C2 `91.219.236.18`, escalates via **`sudo` (`USER_CMD`, `euid=0`)** to read `/root` secrets, installs **cron persistence** (`crontab`) and **tampers with auditd** (`CONFIG_CHANGE` removing rules, `systemctl stop auditd`, `rm` of a log). Benign noise is interleaved: a `cron`/`CRED_ACQ` daemon job, an `apt-get`/`git` deploy by the `deploy` user, and a legitimate admin SSH from `dvora` (`52.170.12.45`). Related records are grouped by shared `SerialNumber`. This is the **Linux-foothold step (SSH brute force ~08:50 → `sudo` abuse & persistence ~09:20)** of the cross-table attack scenario.
The sample uses this curated subset of **real** columns: `TimeGenerated`, `Computer`, `RecordType`, `SerialNumber`, `syscall`, `exe`, `comm`, `exit`, `res`, `success`, `auid`, `uid`, `euid`, `acct`, `user`, `addr`, `terminal`, `tty`, `ses`, `pid`, `ppid`, `cwd`, `key`.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · SSH brute force from a single source IP — [T1110](https://attack.mitre.org/techniques/T1110/)
**Hypothesis:** Multiple failed `USER_AUTH` records from one `addr` against several accounts, followed by a success, indicate a successful SSH password-guessing attack.
```kusto
LinuxAuditLog
| where RecordType == "USER_AUTH"
| where isnotempty(addr)
| summarize Failures   = countif(res == "failed"),
            Successes  = countif(res == "success"),
            Accounts   = make_set(acct),
            FirstSeen  = min(TimeGenerated),
            LastSeen   = max(TimeGenerated)
        by Computer, addr
| where Failures >= 5 and Successes >= 1
| sort by Failures desc
```
**Triage:** True positive = many `failed` accounts from one external `addr` (here `185.220.101.2`) ending in a `success`. Benign = a single user mistyping their own password (one account, low count) from a corporate IP.

### H2 · Sensitive credential-file read via execve — [T1003.008](https://attack.mitre.org/techniques/T1003/008/)
**Hypothesis:** A process executing `cat`/`less`/`cp` against `/etc/shadow` (or `/etc/passwd`) is credential access — especially when run by a non-root login user.
```kusto
LinuxAuditLog
| where RecordType in ("SYSCALL", "EXECVE")
| where comm in ("cat", "less", "more", "cp", "head", "tail")
| where key == "cred-access"
| summarize Records = make_set(RecordType), exe = take_any(exe),
            euid = take_any(euid), auid = take_any(auid),
            TimeGenerated = min(TimeGenerated)
        by SerialNumber, Computer, comm
| sort by TimeGenerated asc
```
**Triage:** True positive = `cat` against shadow/passwd by `auid=1004` (`webapp`) outside any package/config workflow. Benign = backup tooling or config-management runs (correlate `auid`/parent `ppid` and the working directory).

### H3 · Download → make-executable → run from /tmp — staged payload — [T1059.004](https://attack.mitre.org/techniques/T1059/004/)
**Hypothesis:** `wget`/`curl` followed by `chmod` and then execution of a binary out of `/tmp` (cwd `/tmp`) in the same session is the classic download-and-execute chain.
```kusto
LinuxAuditLog
| where RecordType == "SYSCALL" and syscall == "execve"
| where comm in ("wget", "curl", "chmod") or exe startswith "/tmp/"
| project TimeGenerated, Computer, ses, comm, exe, cwd, auid, euid, key, SerialNumber
| sort by TimeGenerated asc
```
**Triage:** True positive = same `ses` shows `wget` → `chmod` → `/tmp/payload` within minutes (keys `download-exec`/`exec-prep`/`malware-exec`). Benign = an admin fetching a signed package into a build dir, not `/tmp`, and not chmod-ing it executable.

### H4 · Audit-configuration tampering / privileged log destruction — [T1562.001](https://attack.mitre.org/techniques/T1562/001/)
**Hypothesis:** `CONFIG_CHANGE` (audit rule removal), stopping the `auditd` service, or deleting files under `/var/log` with `euid=0` is defense evasion to blind the SOC.
```kusto
LinuxAuditLog
| where RecordType in ("CONFIG_CHANGE", "SERVICE_STOP")
      or (syscall == "unlink" and cwd startswith "/var/log")
      or key in ("audit-tamper", "defense-evasion")
| project TimeGenerated, Computer, RecordType, comm, exe, cwd, euid, auid, key, SerialNumber
| sort by TimeGenerated asc
```
**Triage:** True positive = `CONFIG_CHANGE` / `systemctl stop` auditd / `rm` in `/var/log` by login user `auid=1004` with `euid=0` shortly after a foothold. Benign = a change-managed patch window run by a known admin session (correlate with an approved change and the admin's `auid`).

## 🔗 Correlates with
- **Heartbeat** on `Computer` — confirm WEB-APP-01 was reporting, and spot the agent going silent right after the `auditd` tamper (a blinding tell).
- **Syslog** on `Computer` (+ time) — corroborate the SSH auth burst from `sshd`/PAM and the `sudo`/cron activity from the system logger's side.
- **SigninLogs / DeviceLogonEvents** on `addr`→`IPAddress`/`RemoteIP` — tie attacker IP `185.220.101.2` here to the same IP elsewhere in Operation Quiet Ledger (Entra risky sign-in, FIN-WS-07 RDP).
- **DeviceNetworkEvents / VMConnection** on `Computer` + the C2 IP `91.219.236.18` — corroborate the outbound beacon the `/tmp/payload` `connect` syscall recorded.

## 📚 References
- [LinuxAuditLog — Azure Monitor reference](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/linuxauditlog)
- [Collect Syslog and Linux audit data with Azure Monitor Agent / Defender for Cloud](https://learn.microsoft.com/en-us/azure/azure-monitor/agents/data-collection-syslog)
- [The Linux Audit System — record types and field reference (auditd)](https://github.com/linux-audit/audit-documentation/wiki/SPEC-Writing-Good-Events)
