# CommonSecurityLog

> **Category:** Security (CEF — Common Event Format)
> **Connector / source:** Microsoft Sentinel **Common Event Format (CEF) via AMA** connector — a Linux **log forwarder** running the Azure Monitor Agent receives Syslog/CEF messages from security appliances (firewalls, proxies, IPS/IDS, WAFs, email/web gateways) and ships the parsed CEF into this table. The legacy CEF-via-Log-Analytics-agent path writes the same schema.
> **Table plan:** Basic-eligible — the reference flags **Basic log = Yes** (also supports ingestion-time DCR and lake-only ingestion). Commonly kept on **Analytics** so scheduled analytic rules and full KQL run against perimeter telemetry.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/commonsecuritylog

## What this table is
Each row is a single **CEF event** emitted by a network security appliance — a firewall allow/deny, a proxy/URL-filtering verdict, an IPS/IDS hit, a VPN session, a WAF block, and so on — normalized into Common Event Format and forwarded through a Linux collector to Sentinel. The appliance is identified by `DeviceVendor` / `DeviceProduct` / `DeviceVersion` (e.g. `Palo Alto Networks` / `PAN-OS`), the event type by `DeviceEventClassID` + `Activity`, and the verdict by **`DeviceAction`** (allow/deny/drop/reset). Connection facts live in `SourceIP`/`SourcePort` → `DestinationIP`/`DestinationPort` with `Protocol`/`ApplicationProtocol`, byte counts in `SentBytes`/`ReceivedBytes`, and the forwarder host in `Computer`. Rows appear within seconds to a couple of minutes of the appliance generating the event (subject to Syslog/AMA buffering). In a SOC this is the primary **perimeter / north-south** table — used for egress-exfiltration hunting (large `SentBytes`), command-and-control and known-bad-IP detection, blocked-vs-allowed analysis after an IOC update, brute-force and scanning detection, and as the firewall corroboration layer for endpoint and identity alerts.

## Schema
Full column list, validated against the Microsoft Learn reference. (Types are the KQL/Log Analytics types: string, int, long, real, datetime, bool, dynamic, guid.)

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | Event collection time in UTC (when the record reached the collector/workspace). Primary event time — the appliance's own time is `ReceiptTime`/`StartTime`/`EndTime`. |
| DeviceVendor | string | Vendor portion of the appliance identity (e.g. `Palo Alto Networks`, `Check Point`, `Fortinet`, `Cisco`). With product+version, uniquely identifies the sending device type. |
| DeviceProduct | string | Product portion of the appliance identity (e.g. `PAN-OS`, `FortiGate`, `Firepower`). |
| DeviceVersion | string | Version portion of the appliance identity. |
| DeviceEventClassID | string | Unique identifier **per event type** assigned by the appliance — string **or** integer (e.g. `traffic`, `threat`, `4688`, a signature ID). The appliance's event class. |
| Activity | string | Human-readable description of the event (the CEF "name"). |
| LogSeverity | string | Importance of the event. **String** — valid strings `Unknown`/`Low`/`Medium`/`High`/`Very-High`; integer values `0-3`=Low, `4-6`=Medium, `7-8`=High, `9-10`=Very-High may also appear as text. |
| OriginalLogSeverity | string | The non-normalized severity straight from the device (e.g. `Warning`/`Critical`/`Info`) before mapping to the `LogSeverity` Low/Medium/High scale. |
| **DeviceAction** | string | **The action the appliance took** — `allow`, `deny`, `drop`, `reset`, `block`, etc. **This is the verdict column, not `Action`.** |
| SimplifiedDeviceAction | string | A normalized/mapped version of `DeviceAction` (e.g. `Denied` → `Deny`). Useful for cross-vendor grouping; may be empty. |
| SourceIP | string | Source IPv4 address the event refers to. **String** (use `parse_ipv4()` / `ipv4_*` functions to compare ranges). |
| SourcePort | int | Source port. **Integer**, 0–65535. |
| SourceHostName | string | Source FQDN/hostname, when available. |
| SourceUserName | string | Source user, by name. Email addresses are also mapped here; for an inbound connection the remote/sender side. **No separate UPN column** — UPNs land here. |
| SourceUserID | string | Source user by ID. |
| SourceUserPrivileges | string | Source user's privileges (`Administrator`/`User`/`Guest`). |
| SourceMACAddress | string | Source MAC address. |
| SourceNTDomain | string | Windows domain name for the source address. |
| SourceDnsDomain | string | DNS-domain part of the source FQDN. |
| SourceServiceName | string | The service responsible for generating the event on the source. |
| SourceTranslatedAddress | string | Translated (NAT) source address, IPv4. |
| SourceTranslatedPort | int | Translated source port (e.g. after firewall NAT), 0–65535. |
| SourceProcessId | int | ID of the source process associated with the event. |
| SourceProcessName | string | Name of the source process. |
| DestinationIP | string | Destination IPv4 address the event refers to. **String.** |
| DestinationPort | int | Destination port. **Integer**, 0–65535. |
| DestinationHostName | string | Destination FQDN/hostname, when available. |
| DestinationUserName | string | Destination user, by name. (For an inbound RDP/SSH allow, the local account being accessed.) |
| DestinationUserID | string | Destination user by ID (e.g. Unix root = `0`). |
| DestinationUserPrivileges | string | Destination user's privileges (`Administrator`/`User`/`Guest`). |
| DestinationMACAddress | string | Destination MAC address. |
| DestinationNTDomain | string | Windows domain name of the destination address. |
| DestinationDnsDomain | string | DNS-domain part of the destination FQDN. |
| DestinationServiceName | string | Service targeted by the event (e.g. `sshd`). |
| DestinationTranslatedAddress | string | Translated (NAT) destination address, IPv4. |
| DestinationTranslatedPort | int | Translated destination port, 0–65535. |
| DestinationProcessId | int | ID of the destination process associated with the event. |
| DestinationProcessName | string | Name of the destination process (e.g. `sshd`, `telnetd`). |
| Protocol | string | Layer-4 transport protocol — `TCP`, `UDP`, etc. |
| ApplicationProtocol | string | Application-layer protocol — `HTTP`, `HTTPS`, `SSHv2`, `Telnet`, `POP`, `IMAP`, etc. |
| RequestURL | string | URL accessed for an HTTP request, including scheme. The proxy/URL-filtering target. |
| RequestMethod | string | HTTP method used (`GET`, `POST`, …). |
| RequestClientApplication | string | User-Agent associated with the request. |
| RequestContext | string | Origin of the request (e.g. HTTP Referrer). |
| RequestCookies | string | Cookies associated with the request. |
| SentBytes | long | **Bytes transferred outbound.** The egress-volume field for exfiltration hunting. |
| ReceivedBytes | long | Bytes transferred inbound. |
| EventCount | int | How many times the same event was observed (aggregation count). |
| EventType | int | CEF event type: `0` base, `1` aggregated, `2` correlation, `3` action. |
| EventOutcome | string | Outcome of the event, usually `success` / `failure`. |
| CommunicationDirection | string | Direction of the observed communication. Valid values: `0` = Inbound, `1` = Outbound. |
| Computer | string | The **log forwarder / collector** host (from Syslog) — *not* the appliance and *not* the endpoint. The machine running AMA. |
| CollectorHostName | string | Hostname of the collector machine running the agent. |
| DeviceName | string | FQDN associated with the device node generating the event, when available. |
| DeviceAddress | string | IPv4 address of the device generating the event. |
| DeviceExternalID | string | Name that uniquely identifies the device generating the event. |
| DeviceInboundInterface | string | Interface on which the packet/data entered the device (e.g. `ethernet1/2`). |
| DeviceOutboundInterface | string | Interface on which the packet/data left the device. |
| DeviceEventCategory | string | Category assigned by the originating device (vendor's own scheme, e.g. `/Monitor/Disk/Read`). |
| DeviceFacility | string | Syslog facility generating the event (e.g. `auth`, `local1`). |
| Reason | string | Reason an event was generated (e.g. `bad password`, an error/return code). |
| Message | string | Free-text message giving more detail about the event. |
| AdditionalExtensions | string | Placeholder for additional CEF key-value pairs that don't map to a named column. Parse with `extract()`/`parse_csv` style logic. |
| ReceiptTime | string | Time the event was received **by the appliance** (distinct from `TimeGenerated`, which is collector/workspace time). String. |
| StartTime | datetime | When the activity the event refers to started. |
| EndTime | datetime | When the activity related to the event ended. |
| ExternalID | int | *Soon-to-be-deprecated* legacy event ID — replaced by `ExtID`. |
| ExtID | string | ID used by the originating device (replaces legacy `ExternalID`). |
| MaliciousIP | string | If an IP in the message matched the workspace TI feed, it surfaces here. (Plus `MaliciousIPCountry`, `MaliciousIPLatitude`, `MaliciousIPLongitude`, `IndicatorThreatType`, `ThreatConfidence`, `ThreatDescription`, `ThreatSeverity` (int), `ReportReferenceLink` — the TI-enrichment set.) |
| ProcessID | int | ID of the process on the device generating the event. |
| ProcessName | string | Process name associated with the event (e.g. the syslog-generating process on UNIX). |
| RemoteIP | string | Remote IP derived from the event's direction, when possible. |
| RemotePort | string | Remote port derived from the event's direction. **String here** (note: `SourcePort`/`DestinationPort` are int). |
| SourceSystem | string | Type of agent that collected the event (`Linux` for CEF/Syslog collectors). |
| TenantId | string | The Log Analytics workspace ID. |
| Type | string | The name of the table (`CommonSecurityLog`). |
| _ResourceId | string | ARM resource ID associated with the record (the collector VM, when applicable). |

> Full reference table is **130+ columns**. Every detection-relevant field (appliance identity, action/verdict, source/dest IP/port/user, protocols, URL, byte counts, severity, direction, collector, interfaces, TI-enrichment, timestamps) is listed above. The remainder are **device-custom / flex / file mapping** slots that vary per vendor and are mostly empty in practice — they appear in the table tail as: `DeviceCustomString1..6` (+ `…Label`), `DeviceCustomNumber1..3` (int, deprecated → `FieldDeviceCustomNumber1..3` (long)), `DeviceCustomFloatingPoint1..4` (real, + `…Label`), `DeviceCustomDate1..2` (+ `…Label`), `DeviceCustomIPv6Address1..4` (+ `…Label`); `FlexString1..2`, `FlexNumber1..2` (int), `FlexDate1` (all + `…Label`); the file set `FileName`/`FilePath`/`FileHash`/`FileID`/`FileSize` (int)/`FileType`/`FilePermission`/`FileCreateTime`/`FileModificationTime` and the `OldFile*` twins; `DevicePayloadId`, `DeviceTimeZone`, `DeviceDnsDomain`, `DeviceMacAddress`, `DeviceNtDomain`, `DeviceTranslatedAddress`; and the envelope/billing columns `_BilledSize` (real), `_IsBillable` (string), `_SubscriptionId`. Never assume a custom-string column holds a particular value without confirming the vendor's CEF mapping.

## Key columns for detection & hunting
- **Identity:** `SourceUserName` / `DestinationUserName` (by name; UPNs and email addresses are mapped here — there is **no** dedicated UPN column), with `SourceUserID` / `DestinationUserID` for ID-based attribution. Most pure-network appliance rows have **no** user at all.
- **Host / device:** the **appliance** is `DeviceVendor` + `DeviceProduct` + `DeviceVersion` (and `DeviceName`/`DeviceAddress`); the **collector** is `Computer` / `CollectorHostName`. Endpoints are only represented by their IPs (`SourceIP`/`DestinationIP`) — join out to get a hostname.
- **Network:** `SourceIP` / `SourcePort` (int) → `DestinationIP` / `DestinationPort` (int), `Protocol` (L4), `ApplicationProtocol` (L7), `RequestURL` (proxy target), `SentBytes` / `ReceivedBytes` (long), `CommunicationDirection` (0=In/1=Out), `DeviceInboundInterface` / `DeviceOutboundInterface`.
- **Outcome / result:** **`DeviceAction`** (allow/deny/drop/reset — the verdict) and `SimplifiedDeviceAction` (normalized); `EventOutcome` (`success`/`failure`); severity in `LogSeverity` (string) / `OriginalLogSeverity`.
- **Timestamps:** `TimeGenerated` (collector/workspace, UTC — query on this); `ReceiptTime` (appliance receive time, **string**); `StartTime` / `EndTime` (activity span, datetime).
- **Join keys (to other tables):** `SourceIP` / `DestinationIP` ↔ IP columns elsewhere (`IPAddress`, `RemoteIP`, `CallerIpAddress` (port-stripped)); `SourceUserName` / `DestinationUserName` ↔ `UserPrincipalName` / `AccountUpn`; `DestinationHostName` ↔ `DeviceName` / `Computer`; `RequestURL`/`DestinationIP` ↔ DNS-resolved domains/IPs. **No `CorrelationId` in this table** — pivots are on IP / user / time.

## ⚠️ Schema gotchas
- **The action is `DeviceAction`, not `Action`.** A surprising amount of copy-pasted KQL references a non-existent `Action` column. The verdict is `DeviceAction` (raw: `allow`/`deny`/`drop`/…); use `SimplifiedDeviceAction` only for cross-vendor normalization, and note it can be empty.
- **Ports are `int`, but `RemotePort` is a `string`.** `SourcePort` and `DestinationPort` are integers (compare numerically); `RemotePort` is a string. Don't mix them in a single comparison without casting.
- **IPs are `string`.** `SourceIP`/`DestinationIP` are string columns — use `parse_ipv4()`, `ipv4_is_in_range()`, `ipv4_is_private()` for CIDR/range logic; `==` works for exact matches.
- **`SentBytes`/`ReceivedBytes` are `long` and direction-relative.** "Sent" is **outbound** — for egress/exfil sum `SentBytes`. Some appliances under-report or zero the byte counts on a `deny`; coalesce (`coalesce(SentBytes, 0L)`) before summing, and don't read a 0-byte denied connection as "no data."
- **`LogSeverity` is a `string`.** It holds `Low`/`Medium`/`High`/`Very-High` (or a numeric string) — never compare it as an int directly; map or `toint()` deliberately.
- **`Computer` is the forwarder, not the source host.** It is the Linux AMA collector. The actual endpoints are only their IPs in `SourceIP`/`DestinationIP`.
- **No `CorrelationId`.** Unlike `StorageBlobLogs` / `AzureActivity`, CEF rows carry no correlation GUID — correlate by IP, user, URL, and time window instead. `ExternalID` is being deprecated in favour of `ExtID`.
- **Vendor variance.** Field population differs sharply by appliance. Palo Alto fills `DeviceEventClassID` with `traffic`/`threat`; other vendors use numeric signature IDs and lean on `DeviceCustomString*`. Confirm the mapping for the actual `DeviceVendor`/`DeviceProduct` before trusting a custom field.

## 🧪 Sample data
[`CommonSecurityLog_sample.csv`](CommonSecurityLog_sample.csv) — 23 rows. Palo Alto (`PAN-OS`) firewall CEF for the **perimeter view of "Operation Quiet Ledger"** on 2026-06-10: benign business HTTPS to Microsoft 365 (`52.170.12.45`/`20.98.111.30`) by `meganb`/`jamest`/`dvora`/`itadmin` spread across the morning, then the attacker IP **`185.220.101.2`** opening **inbound RDP allowed to FIN-WS-07** (`10.50.12.7:3389`, ~08:21–08:35) and an **SSH brute force → login on WEB-APP-01** (`10.50.20.11:22`, ~08:51), the **C2 channel to `badupdate-cdn.com`/`91.219.236.18`** (some `deny`, some `allow`; ~09:15–10:41), and the **large outbound transfer (high `SentBytes`)** to `stcontosofin.blob.core.windows.net` at **~10:18–10:24** that coincides with the blob exfil — a 512 MB GL export, a 256 MB statement archive, a 73 MB customer-master, plus a 275 MB push straight to the C2. This is the **C2/egress + exfil-egress slice (~09:15–10:40)** of the incident, the firewall corroboration for the `StorageBlobLogs` burst and the `SigninLogs` risky sign-in.

The sample uses this curated subset of **real** columns: `TimeGenerated`, `DeviceVendor`, `DeviceProduct`, `DeviceVersion`, `Computer`, `DeviceEventClassID`, `Activity`, `LogSeverity`, `DeviceAction`, `SourceIP`, `SourcePort`, `DestinationIP`, `DestinationPort`, `SourceUserName`, `DestinationUserName`, `Protocol`, `ApplicationProtocol`, `RequestURL`, `SentBytes`, `ReceivedBytes`, `DeviceInboundInterface`, `DeviceOutboundInterface`.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · High outbound volume (SentBytes) by source IP — [T1567](https://attack.mitre.org/techniques/T1567/)
**Hypothesis:** An internal host that pushes an unusually large total of outbound bytes through the firewall in a short window — well above normal business traffic — is exfiltrating data over the network.
```kusto
CommonSecurityLog
| where DeviceAction in ("allow", "block", "deny")   // count attempted volume, not just permitted
| summarize TotalSent = sum(coalesce(SentBytes, 0L)),
            Sessions = count(),
            Dests = dcount(DestinationIP),
            URLs = make_set(RequestURL, 10),
            FirstSeen = min(TimeGenerated), LastSeen = max(TimeGenerated)
    by SourceIP
| extend TotalSentMB = round(TotalSent / 1048576.0, 1)
| where TotalSentMB > 100
| sort by TotalSent desc
```
**Triage:** True positive = `10.50.12.7` (FIN-WS-07) sending hundreds of MB outbound to `stcontosofin.blob.core.windows.net` and to `91.219.236.18` over a few minutes around 10:20, no business justification. Benign = a sanctioned backup/replication job or a large legitimate upload to a known SaaS endpoint — confirm the destination and the user.

### H2 · Connections to / from a known-bad IP — [T1071.001](https://attack.mitre.org/techniques/T1071.001/)
**Hypothesis:** Any firewall event whose source or destination matches a known attacker IP (threat-intel hit) indicates inbound access or outbound C2 — whether the appliance allowed or blocked it.
```kusto
let badIPs = dynamic(["185.220.101.2", "91.219.236.18"]);
CommonSecurityLog
| where SourceIP in (badIPs) or DestinationIP in (badIPs)
| extend Direction = iff(SourceIP in (badIPs), "inbound-from-bad", "outbound-to-bad")
| project TimeGenerated, Direction, DeviceAction, SourceIP, SourcePort,
          DestinationIP, DestinationPort, SourceUserName, DestinationUserName,
          ApplicationProtocol, RequestURL, SentBytes, ReceivedBytes, Activity, LogSeverity
| sort by TimeGenerated asc
```
**Triage:** True positive = inbound RDP `allow` from `185.220.101.2` to `10.50.12.7:3389`, SSH login to `10.50.20.11:22`, and repeated `badupdate-cdn.com`/`91.219.236.18` beacons (mix of allow/deny). Benign = a blocked one-off scan with no follow-on session — but any **allowed** connection to/from these IPs is actionable.

### H3 · Allowed C2 after some blocks (URL-filtering gaps) — [T1071](https://attack.mitre.org/techniques/T1071/)
**Hypothesis:** A destination domain/IP that the firewall sometimes blocks and sometimes allows reveals a C2 channel that beat URL filtering before an IOC update — the *allowed* beacons are the live channel.
```kusto
CommonSecurityLog
| where ApplicationProtocol in ("HTTP", "HTTPS")
| where RequestURL has "badupdate-cdn.com" or DestinationIP == "91.219.236.18"
| summarize Allowed = countif(DeviceAction == "allow"),
            Denied = countif(DeviceAction in ("deny", "drop", "block")),
            SentOut = sum(coalesce(SentBytes, 0L)),
            FirstSeen = min(TimeGenerated), LastSeen = max(TimeGenerated)
    by SourceIP, DestinationIP, tostring(split(RequestURL, "?")[0])
| where Allowed > 0
| sort by SentOut desc
```
**Triage:** True positive = `10.50.12.7 → 91.219.236.18` with several `allow` checkins/tasks before the 10:41 `deny`, including the 275 MB `/upload`. Benign = a freshly mis-categorized but legitimate site briefly allowed then corrected — validate the domain reputation and the volume.

### H4 · Inbound RDP/SSH allowed from the internet — [T1133](https://attack.mitre.org/techniques/T1133/)
**Hypothesis:** Any **allowed** inbound session on a remote-admin port (3389/RDP, 22/SSH) from a public source IP is an external-remote-services exposure and a prime initial-access vector.
```kusto
CommonSecurityLog
| where DeviceAction == "allow"
| where DestinationPort in (3389, 22)
| where not(ipv4_is_private(SourceIP))
| project TimeGenerated, ApplicationProtocol, SourceIP, SourcePort,
          DestinationIP, DestinationPort, DestinationUserName, Activity,
          SentBytes, ReceivedBytes, LogSeverity
| sort by TimeGenerated asc
```
**Triage:** True positive = `185.220.101.2` → `10.50.12.7:3389` (RDP to FIN-WS-07) and → `10.50.20.11:22` (SSH to WEB-APP-01 after a brute-force burst). Benign = a documented jump-host/bastion source IP or a maintenance window — confirm the source IP is an approved admin origin.

## 🔗 Correlates with
- **StorageBlobLogs** on `DestinationIP`/`RequestURL` ↔ `AccountName`/`Uri` and on **time** — the large outbound `SentBytes` to `stcontosofin.blob.core.windows.net` at ~10:18–10:24 is the firewall-side view of the same blob `GetBlob` exfil burst; the firewall sees the bytes and the URL, the storage log sees the AccountKey caller.
- **SigninLogs** on `SourceIP` ↔ `IPAddress` — tie the attacker IP `185.220.101.2` at the perimeter to the risky Entra sign-in for `alexw` from the Netherlands (~08:20); the firewall confirms the same IP held an inbound RDP session to the workstation.
- **DnsEvents** on `DestinationIP`/`RequestURL` ↔ resolved domain — pair the `badupdate-cdn.com` C2 lookups (~09:15) with the firewall's allow/deny of the subsequent HTTPS beacons to `91.219.236.18`.
- **DeviceNetworkEvents** on `DestinationIP` ↔ `RemoteIP` / `SourceIP` ↔ `LocalIP` — the same C2 IP (`91.219.236.18`) and attacker IP (`185.220.101.2`) observed beaconing from / connecting to FIN-WS-07 at the endpoint, corroborating the perimeter verdict. *(Endpoint table; pivot on IP + time — this table is not yet in the library.)*

## 📚 References
- CommonSecurityLog table reference — https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/commonsecuritylog
- CEF via AMA connector for Microsoft Sentinel — https://learn.microsoft.com/en-us/azure/sentinel/connect-cef-ama
- CEF field mapping for Microsoft Sentinel — https://learn.microsoft.com/en-us/azure/sentinel/cef-name-mapping
