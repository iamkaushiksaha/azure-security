# Syslog

> **Category:** Security / Virtual Machines (Linux host telemetry)
> **Connector / source:** Azure Monitor Agent (AMA) **Syslog** data connector, or the legacy Log Analytics agent (OMS), forwarding the host's RFC 3164/5424 syslog stream from Linux VMs, Arc-enabled servers, and AKS/Arc clusters into the workspace.
> **Table plan:** Analytics (default). The reference flags **Basic log: No**; it does support ingestion-time DCR transforms and lake-only ingestion.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/syslog

## What this table is
Each row is a **single Linux syslog message** captured from a host's `rsyslog`/`syslog-ng` daemon and shipped to the workspace by the Azure Monitor Agent (or legacy Log Analytics agent). A row records which daemon emitted the line (`Facility` + `ProcessName`/`ProcessID`), how severe it is (`SeverityLevel`), which host it came from (`Computer` / `HostName` / `HostIP`), and — crucially — the **raw message text in `SyslogMessage`**. Rows appear continuously as configured facilities (auth, authpriv, cron, daemon, kern, …) log activity. In a SOC it is the primary Linux-side source for **SSH brute-force / authentication-failure detection, sudo/su privilege-escalation tracking, and persistence hunting (new users, cron edits)** — but because almost all the security signal lives in free-text `SyslogMessage`, nearly every hunt must `parse`/`extract` that field.

## Schema
Full column list, validated against the Microsoft Learn reference. Types are KQL/Log Analytics types.

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | Date and time the record was created (ingestion timestamp in the workspace). |
| EventTime | datetime | Date and time the event was generated on the host (the syslog line's own timestamp). |
| Computer | string | Computer from which the event originated. |
| HostName | string | Name of the system from which the message originated (host-reported name; may differ from `Computer`). |
| HostIP | string | IP address of the system from which the message originated. May be blank or a placeholder depending on network topology, especially for messages relayed from a remote device. |
| Facility | string | The part of the system that generated the message (`auth`, `authpriv`, `cron`, `daemon`, `kern`, `mail`, `user`, `local0`–`local7`, …). |
| SeverityLevel | string | Severity level of the event (`emerg`, `alert`, `crit`, `err`, `warning`, `notice`, `info`, `debug`). |
| ProcessName | string | Name of the process/daemon that generated the message (e.g. `sshd`, `sudo`, `su`, `CRON`, `systemd`). |
| ProcessID | int | ID of the process that generated the message. |
| SyslogMessage | string | **Free text of the message** — usernames, source IPs, commands, and outcomes are embedded here, not in dedicated columns. |
| CollectorHostName | string | Name of the system on which the collector agent is installed (set when a forwarder/relay collects on behalf of other hosts). |
| SourceSystem | string | Type of agent the event was collected by — `Linux` for all Linux agents. |
| _ResourceId | string | Unique identifier for the Azure resource the record is associated with. |
| _SubscriptionId | string | Unique identifier for the subscription the record is associated with. |
| Type | string | The name of the table (`Syslog`). |

> **Total: 17 columns** (the 15 above plus the billing/system columns `_BilledSize` (real) and `_IsBillable` (string)). No column was invented. `SyslogMessage` is plain text, **not** a dynamic/JSON blob — there are no nested columns in this table.

## Key columns for detection & hunting
- **Identity:** **There is no identity column.** The acting user, target user, and any source/remote user live inside `SyslogMessage` and must be pulled out with `extract()` / `parse` (e.g. `extract(@"for (?:invalid user )?(\S+)", 1, SyslogMessage)` for the sshd target user; `extract(@"^\s*(\S+) : ", 1, SyslogMessage)` for the sudo invoking user).
- **Host / device:** `Computer` and `HostName` (host name), `HostIP` (originating host IP). `CollectorHostName` only when a relay/forwarder is in play.
- **Network:** **No source/dest IP columns.** The attacker's remote IP (e.g. `185.220.101.2`) and port appear *inside* `SyslogMessage` for `sshd` lines — extract with `extract(@"from (\d{1,3}(?:\.\d{1,3}){3})", 1, SyslogMessage)`.
- **Outcome / result:** **No result column.** Success/failure is text in `SyslogMessage`: `Failed password` / `Accepted password` / `authentication failure` / `Successful su`. Filter with `has`/`contains`/`matches regex`.
- **Timestamps:** `TimeGenerated` (workspace ingestion) and `EventTime` (host-side event time). Prefer `EventTime` for on-host sequencing; they can diverge under ingestion lag.
- **Join keys (to other tables):** `Computer` / `HostName` (→ `Heartbeat`, `VMConnection`, `Update`, other host tables), `HostIP` (→ network tables), and **values extracted from `SyslogMessage`** — the source IP (→ `SigninLogs.IPAddress`, `DeviceNetworkEvents.RemoteIP`) and the username (→ Windows `SecurityEvent` / Entra `SigninLogs` after mapping).

## ⚠️ Schema gotchas
- **The security signal is in free text.** `SyslogMessage` holds the username, source IP, command, and outcome — there is **no** `UserPrincipalName`, `AccountName`, `CommandLine`, `RemoteIP`, or `Status` column. Every meaningful hunt parses this string; do not look for dedicated fields that don't exist.
- **`SeverityLevel` is a STRING, not an int**, and it is the *syslog* severity word (`info`, `notice`, `warning`, `err`, …) — **not** the numeric facility/priority. Compare against strings (`SeverityLevel == "err"`), not numbers. Note an authentication *failure* is commonly logged at `info`/`notice`, so severity is a poor proxy for "bad".
- **`Facility` vs `ProcessName` are different axes.** SSH logins are `Facility == "authpriv"` (or `auth`), while the daemon is `ProcessName == "sshd"`. Filter on both — many hosts route the same daemon's lines across `auth` and `authpriv`.
- **`Computer` vs `HostName` can differ**, and `HostIP` may be **blank or a placeholder** for messages relayed through a forwarder (`CollectorHostName` set). Don't assume `HostIP` is always populated or that it is the *attacker's* IP — it is the *originating host's* IP.
- **`ProcessID` (int) is reused** across the OS lifetime and is only locally meaningful between restarts; never treat it as a global unique key.

## 🧪 Sample data
[`Syslog_sample.csv`](Syslog_sample.csv) — 30 rows. The rows tell the **Operation Quiet Ledger** Linux-foothold story on **WEB-APP-01** (Ubuntu 22.04): an `sshd` **brute-force burst from `185.220.101.2`** (~08:50 — `Failed password for invalid user …` across `admin`/`oracle`/`postgres`/`deploy`/`git`, plus `Failed password for root`) culminating in `Accepted password for webadmin`, then **privilege escalation** (`sudo … COMMAND=/bin/su -`, `Successful su for root`) and **persistence** (`useradd svc-deploy`, add to `sudo` group, root `crontab REPLACE`), interleaved with benign `cron`/`systemd`/`dockerd` noise and two benign Linux lines from `DC01`/`FIN-WS-07`.
The sample uses this curated subset of **real** columns: `TimeGenerated`, `Computer`, `HostName`, `HostIP`, `Facility`, `SeverityLevel`, `ProcessName`, `ProcessID`, `SyslogMessage`, `EventTime`, `SourceSystem`. This is the **Linux foothold step (~08:50 SSH brute force → ~09:20 sudo/su abuse and persistence on WEB-APP-01)** of the cross-table attack scenario.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · SSH brute force — failed-password burst then an accepted password — [T1110](https://attack.mitre.org/techniques/T1110/)
**Hypothesis:** Many `Failed password` events from one source IP against a host, followed by an `Accepted password` from that same IP, indicates a successful SSH credential-guessing attack. The source IP is **parsed out of `SyslogMessage`**.
```kusto
Syslog
| where ProcessName == "sshd"
| extend SrcIP = extract(@"from (\d{1,3}(?:\.\d{1,3}){3})", 1, SyslogMessage)
| where isnotempty(SrcIP)
| summarize Failed   = countif(SyslogMessage has "Failed password"),
            Accepted = countif(SyslogMessage has "Accepted password"),
            TargetedUsers = dcount(extract(@"for (?:invalid user )?(\S+)", 1, SyslogMessage)),
            FirstSeen = min(EventTime), LastSeen = max(EventTime)
        by Computer, SrcIP
| where Failed >= 5 and Accepted >= 1
| sort by Failed desc
```
**Triage:** True positive = a single `SrcIP` (here `185.220.101.2`) with a high `Failed` count and broad `TargetedUsers` fan-out ending in `Accepted` on `WEB-APP-01`. Benign = a known automation host with one or two mistyped logins and no invalid-user spray.

### H2 · `sudo` to root running a suspicious command — [T1548.003](https://attack.mitre.org/techniques/T1548/003/)
**Hypothesis:** A `sudo` line whose target user is `root` and whose `COMMAND=` is a shell, package install, or download tool indicates privilege escalation or tool staging. Invoking user and command are **extracted from `SyslogMessage`**.
```kusto
Syslog
| where ProcessName == "sudo" and SyslogMessage has "COMMAND="
| extend InvokingUser = extract(@"^\s*(\S+)\s*:", 1, SyslogMessage),
         TargetUser   = extract(@"USER=(\S+)", 1, SyslogMessage),
         Command      = extract(@"COMMAND=(.+)$", 1, SyslogMessage)
| where TargetUser == "root"
| where Command has_any ("/bin/su", "/bin/bash", "/bin/sh", "apt-get", "yum", "curl", "wget", "nc", "netcat")
| project EventTime, Computer, InvokingUser, TargetUser, Command, SyslogMessage
| sort by EventTime asc
```
**Triage:** True positive = `webadmin` escalating to `root` to install `netcat` and spawn `su -` on `WEB-APP-01` shortly after a suspicious SSH login. Benign = a sanctioned admin running routine `apt-get`/maintenance from an expected account and session.

### H3 · New local user created and added to a privileged group — [T1136.001](https://attack.mitre.org/techniques/T1136/001/)
**Hypothesis:** A `useradd`/`usermod` event creating an account and granting it `sudo`/`wheel`/`root` membership on a server is a hallmark of post-compromise persistence.
```kusto
Syslog
| where ProcessName in ("useradd", "usermod")
| where SyslogMessage has_any ("new user", "add", "to group")
| where SyslogMessage has_any ("sudo", "wheel", "root", "admin")
      or ProcessName == "useradd"
| extend NewUser = coalesce(extract(@"name=(\S+?),", 1, SyslogMessage),
                            extract(@"'([^']+)' to group", 1, SyslogMessage)),
         Group   = extract(@"to group '([^']+)'", 1, SyslogMessage)
| project EventTime, Computer, ProcessName, NewUser, Group, SyslogMessage
| sort by EventTime asc
```
**Triage:** True positive = a backdoor account (here `svc-deploy`) created and added to `sudo` on `WEB-APP-01` within the intrusion window. Benign = provisioning automation or a ticketed onboarding from an approved configuration-management run.

### H4 · `su` session opened to root — interactive root escalation — [T1078.003](https://attack.mitre.org/techniques/T1078/003/)
**Hypothesis:** A `pam_unix(su…): session opened for user root` or `Successful su for root` line shows an interactive switch to the root account; correlating the invoking user back to a freshly-authenticated SSH session tightens the case.
```kusto
Syslog
| where ProcessName == "su"
| where SyslogMessage has "root" and (SyslogMessage has "session opened" or SyslogMessage has "Successful su")
| extend ByUser = coalesce(extract(@"by (\S+?)\(uid=", 1, SyslogMessage),
                           extract(@"by (\S+)$", 1, SyslogMessage))
| project EventTime, Computer, ProcessName, ByUser, SyslogMessage
| sort by EventTime asc
```
**Triage:** True positive = `webadmin` opening a root `su` session on `WEB-APP-01` right after the brute-forced login. Benign = a named admin using `su` as part of normal break-glass on a host where that is expected.

## 🔗 Correlates with
- **Heartbeat** on `Computer` — confirm `WEB-APP-01` was reporting (and watch for it dropping off after compromise) and resolve its Azure resource / IP.
- **SecurityEvent / DeviceLogonEvents** on the **username extracted from `SyslogMessage`** (`webadmin`→account) and on `HostIP` — tie the Linux foothold to the Windows side of the same intrusion (FIN-WS-07/DC01 lateral movement).
- **SigninLogs** on the **source IP extracted from `SyslogMessage`** (`185.220.101.2`→`IPAddress`) — link the SSH brute force to the same attacker IP seen in the Entra risky sign-ins for `alexw`.
- **VMConnection / DeviceNetworkEvents** on `Computer` / `HostIP` + the extracted source IP — corroborate the inbound TCP/22 connections behind the `sshd` events.

## 📚 References
- [Syslog — Azure Monitor Logs table reference](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/syslog)
- [Collect Syslog events with Azure Monitor Agent](https://learn.microsoft.com/en-us/azure/azure-monitor/agents/data-collection-syslog)
- [Syslog record properties (legacy Log Analytics agent)](https://learn.microsoft.com/en-us/azure/azure-monitor/agents/data-sources-syslog)
