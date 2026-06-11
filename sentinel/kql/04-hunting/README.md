# Stage 04 · Threat Hunting with KQL — MITRE-mapped hunts

> **Audience:** threat hunters and detection engineers.
> **Tables:** real Sentinel / Defender XDR tables. Each hunt notes the table it needs and the connector that fills it. No data yet? Read the patterns, then practise the *shape* on `DemoIdentityLogs` or an [ADX free cluster](../00-setup/README.md).
> **Mapping:** every hunt is tagged with its [MITRE ATT&CK](https://attack.mitre.org/) technique so you can tie findings to a framework.

Every column below was schema-validated against Microsoft Learn (see [`../reference/ms-reference-links.md`](../reference/ms-reference-links.md)). General hunting references: [Hunt for threats in Sentinel](https://learn.microsoft.com/en-us/azure/sentinel/hunting) · [Advanced hunting in Defender XDR](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-overview).

> **Reminder:** these are **hunting hypotheses, not finished detections**. Thresholds are starting points — tune to your environment, and confirm hits before acting.

---

## A. Identity hunts (`SigninLogs`, `AuditLogs`)

### A1 · Password spray — [T1110.003](https://attack.mitre.org/techniques/T1110/003/)
**Hypothesis:** one source IP attempts a few passwords against **many** accounts (low-and-slow), producing failures spread across users.

```kusto
SigninLogs
| where TimeGenerated > ago(1d)
| where ResultType == "50126"            // invalid username or password
| summarize TargetedUsers = dcount(UserPrincipalName),
            Attempts = count(),
            Users = make_set(UserPrincipalName, 50)
        by IPAddress, AutonomousSystemNumber
| where TargetedUsers >= 5               // tune: many distinct victims from one IP
| sort by TargetedUsers desc
```
**Triage:** is the IP known infrastructure (VPN/gateway)? Did any of those users *succeed* shortly after? Pivot A3.

### A2 · Brute force on a single account — [T1110.001](https://attack.mitre.org/techniques/T1110/001/)
**Hypothesis:** a single account sees a burst of failed sign-ins.

```kusto
SigninLogs
| where TimeGenerated > ago(1d)
| where ResultType != "0"
| summarize Failures = count(),
            SourceIPs = dcount(IPAddress),
            FirstSeen = min(TimeGenerated),
            LastSeen = max(TimeGenerated)
        by UserPrincipalName
| where Failures >= 10
| sort by Failures desc
```

### A3 · Successful sign-in after repeated failures — [T1110](https://attack.mitre.org/techniques/T1110/)
**Hypothesis:** failures followed by a success for the same user = possible breach.

```kusto
let lookback = 1d;
let failures =
    SigninLogs
    | where TimeGenerated > ago(lookback) and ResultType != "0"
    | summarize Failures = count(), LastFailure = max(TimeGenerated) by UserPrincipalName
    | where Failures >= 10;
SigninLogs
| where TimeGenerated > ago(lookback) and ResultType == "0"
| join kind=inner failures on UserPrincipalName
| where TimeGenerated > LastFailure          // success AFTER the failures
| project SuccessTime = TimeGenerated, UserPrincipalName, IPAddress, Location, AppDisplayName, Failures
| sort by SuccessTime desc
```

### A4 · Atypical / impossible travel — [T1078](https://attack.mitre.org/techniques/T1078/)
**Hypothesis:** a user signs in successfully from multiple countries in a short window.

```kusto
SigninLogs
| where TimeGenerated > ago(1d)
| where ResultType == "0"
| summarize Countries = dcount(Location),
            CountrySet = make_set(Location),
            IPs = make_set(IPAddress, 20)
        by UserPrincipalName
| where Countries > 1
| sort by Countries desc
```
**Triage:** corporate VPN or travel can explain this. Combine with `RiskLevelDuringSignIn` for a stronger signal.

### A5 · Risky sign-ins (Identity Protection) — [T1078](https://attack.mitre.org/techniques/T1078/)
**Hypothesis:** Entra ID Protection flagged sign-ins as medium/high risk. *(Requires Entra ID P2 for populated risk fields.)*

```kusto
SigninLogs
| where TimeGenerated > ago(7d)
| where RiskLevelDuringSignIn in ("medium", "high")
| project TimeGenerated, UserPrincipalName, IPAddress, Location, RiskLevelDuringSignIn, AppDisplayName, ResultType
| sort by TimeGenerated desc
```

### A6 · Privilege activity after failed auth — [T1098](https://attack.mitre.org/techniques/T1098/)
**Hypothesis:** a user who struggled to authenticate then performs admin/directory operations.

```kusto
let suspect =
    SigninLogs
    | where TimeGenerated > ago(1d) and ResultType != "0"
    | summarize Failures = count() by UserPrincipalName
    | where Failures > 5;
AuditLogs
| where TimeGenerated > ago(1d)
| extend Actor = tostring(InitiatedBy.user.userPrincipalName)   // InitiatedBy is dynamic
| join kind=inner suspect on $left.Actor == $right.UserPrincipalName
| project TimeGenerated, Actor, OperationName, Result, Failures
| sort by TimeGenerated desc
```

### A7 · Consent to OAuth application — [T1528](https://attack.mitre.org/techniques/T1528/)
**Hypothesis:** consent-phishing grants a malicious app access to a user's data.

```kusto
AuditLogs
| where TimeGenerated > ago(7d)
| where OperationName has "Consent to application"
| extend Actor = tostring(InitiatedBy.user.userPrincipalName)
| extend App = tostring(TargetResources[0].displayName)
| project TimeGenerated, Actor, App, OperationName, Result
| sort by TimeGenerated desc
```

---

## B. Endpoint hunts (`DeviceProcessEvents`, `DeviceNetworkEvents`)

*Requires Microsoft Defender for Endpoint data (the `Device*` tables).*

### B1 · LOLBin execution — [T1218](https://attack.mitre.org/techniques/T1218/)
**Hypothesis:** living-off-the-land binaries used to proxy execution.

```kusto
let lolbins = dynamic(["mshta.exe","regsvr32.exe","rundll32.exe","wmic.exe","certutil.exe","bitsadmin.exe","cscript.exe","wscript.exe"]);
DeviceProcessEvents
| where TimeGenerated > ago(1d)
| where FileName in~ (lolbins)
| project TimeGenerated, DeviceName, AccountName, FileName, ProcessCommandLine,
          InitiatingProcessFileName, InitiatingProcessParentFileName
| sort by TimeGenerated desc
```
**Triage:** legitimate admin/software use is common — anchor on the **command line** and the **parent** process.

### B2 · Office app spawning a script host — [T1566](https://attack.mitre.org/techniques/T1566/) / [T1059](https://attack.mitre.org/techniques/T1059/)
**Hypothesis:** a document weaponised to launch a shell/script interpreter.

```kusto
let officeApps  = dynamic(["winword.exe","excel.exe","powerpnt.exe","outlook.exe"]);
let scriptHosts = dynamic(["powershell.exe","pwsh.exe","cmd.exe","wscript.exe","cscript.exe","mshta.exe"]);
DeviceProcessEvents
| where TimeGenerated > ago(1d)
| where InitiatingProcessFileName in~ (officeApps)
| where FileName in~ (scriptHosts)
| project TimeGenerated, DeviceName, AccountName,
          ParentApp = InitiatingProcessFileName, Spawned = FileName, ProcessCommandLine
| sort by TimeGenerated desc
```

### B3 · Encoded / obfuscated PowerShell — [T1059.001](https://attack.mitre.org/techniques/T1059/001/)
**Hypothesis:** base64-encoded or hidden PowerShell to evade inspection.

```kusto
DeviceProcessEvents
| where TimeGenerated > ago(1d)
| where FileName in~ ("powershell.exe","pwsh.exe")
| where ProcessCommandLine has_any ("-enc","-EncodedCommand","-e ","FromBase64String","-w hidden","-nop","IEX","Invoke-Expression")
| project TimeGenerated, DeviceName, AccountName, ProcessCommandLine,
          InitiatingProcessFileName, InitiatingProcessParentFileName
| sort by TimeGenerated desc
```

### B4 · Suspicious outbound connection by process — [T1071](https://attack.mitre.org/techniques/T1071/)
**Hypothesis:** a process beacons to an external host (possible C2).

```kusto
let interpreters = dynamic(["powershell.exe","pwsh.exe","cmd.exe","wscript.exe","cscript.exe","mshta.exe","rundll32.exe","regsvr32.exe"]);
DeviceNetworkEvents
| where TimeGenerated > ago(1d)
| where RemoteIPType == "Public"
| where InitiatingProcessFileName in~ (interpreters)
| summarize Connections = count(),
            RemoteHosts = make_set(coalesce(RemoteUrl, RemoteIP), 50)
        by DeviceName, InitiatingProcessFileName, InitiatingProcessAccountName
| sort by Connections desc
```
**Triage:** interpreters making public connections is unusual on most endpoints. Pivot to B3 on the same device/command line.

---

## How to run a hunt end-to-end

1. **Pick a hypothesis** (one of the above) and a time window.
2. **Run broad**, eyeball the top results, then **tighten thresholds** to your environment's baseline.
3. **Pivot** on a strong indicator — same user, IP, device, or command line — across tables.
4. **Promote** a high-fidelity hunt into a scheduled **Analytics Rule** (governance: detections live as rules, not ad-hoc queries).
5. **Document** the technique ID, query, and triage notes so the next hunter can reuse it.

> Promote-to-rule and ASIM normalization (Stage 03 §6) make these portable. Where a parser exists, an `_Im_Authentication`/`_Im_NetworkSession` version of A1–A4 / B4 will also catch non-AAD and non-MDE sources.

---

**You've completed the path.** Loop back to the [index](../README.md) for the cheatsheet and schema gotchas.
