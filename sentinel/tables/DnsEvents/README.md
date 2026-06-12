# DnsEvents

> **Category:** Network (Security — Sentinel DNS solution: `DnsAnalytics` / `SecurityInsights`)
> **Connector / source:** **DNS** data connector (legacy MMA/Log Analytics agent DNS extension, or **Windows DNS Events via AMA**). Collects Windows DNS Server analytical + audit logs from domain controllers / DNS servers and uploads the per-query "lookup" records.
> **Table plan:** Analytics (default). The reference flags **Basic log: No**; DCR-at-ingestion and lake-only ingestion are supported.
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/dnsevents

## What this table is
Each row is a **DNS event observed on a Windows DNS server** — overwhelmingly a name-resolution *lookup query* (`SubType == "LookupQuery"`), but the table also carries dynamic-registration and other DNS server events. A lookup row records **which client asked** (`ClientIP`), **the name queried** (`Name`), **the record type** (`QueryType` — A, AAAA, TXT, MX, …), **what was returned** (`IPAddresses`, a comma-joined string), **whether it succeeded** (`ResultCode`, `Result`), and **which DNS server answered** (`Computer`). Rows appear continuously, one per resolved query the server logs. When Sentinel threat-intelligence matching is enabled the connector enriches malicious answers in-line via `MaliciousIP`, `IndicatorThreatType`, and `Confidence`. In a SOC this is the primary source for **C2-over-DNS / beaconing detection, DGA and tunnelling hunts (high-volume TXT / long random labels / NXDOMAIN spikes), and resolving "who looked up this bad domain"** — it is the network-side complement to endpoint process and proxy logs.

## Schema
Full column list, validated against the Microsoft Learn reference. Types are KQL/Log Analytics types. (The reference leaves most descriptions blank; descriptions below are the documented Windows-DNS-Analytics semantics.)

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | When the DNS event was recorded / ingested (UTC). |
| Computer | string | Host name of the **Windows DNS server** that logged the event (e.g. `DC01`). |
| ClientIP | string | IP address of the **client** that issued the DNS query (the requester). |
| Name | string | The **queried name** — the domain/host the client asked the server to resolve. |
| QueryType | string | DNS **record type** requested as a string: `A`, `AAAA`, `TXT`, `MX`, `CNAME`, `PTR`, `SRV`, … |
| IPAddresses | string | The **resolved answer(s)** returned for the query, comma-joined into one string (empty on failure). |
| Result | string | Human-readable result/status of the lookup (e.g. `Success`, `NXDOMAIN`). |
| ResultCode | int | DNS **response code** as an integer. `0` = success (NOERROR); non-zero = failure (Windows DNS uses e.g. `9003` for NXDOMAIN / name does not exist, `9501` no records). |
| SubType | string | DNS event sub-type. The analytical lookup record is `LookupQuery`; other values cover dynamic registration / server events. |
| EventId | int | Windows DNS analytical **event ID** (e.g. `256`/`257` for the lookup request/response path). |
| TaskCategory | string | DNS server task/category label for the event. |
| Message | string | Free-text description of the event as emitted by the DNS server. |
| Description | string | Description text (threat-intel context when an indicator matched, else generic). |
| MaliciousIP | string | If a returned/queried IP matched **threat intelligence**, the offending IP; empty otherwise. |
| IndicatorThreatType | string | Threat type of the matched TI indicator (e.g. `Botnet`, `C2`, `Malware`, `Phishing`). |
| Confidence | string | Confidence score/level of the matched TI indicator. |
| Severity | int | Severity assigned to the event (TI-enriched events carry higher values). |
| RemoteIPCountry | string | Geo country of the remote/answer IP (when geo-enrichment is available). |
| RemoteIPLatitude | real | Latitude of the remote/answer IP. |
| RemoteIPLongitude | real | Longitude of the remote/answer IP. |
| SourceSystem | string | Agent type that collected the event (e.g. `OpsManager` for the Windows agent). |
| Type | string | The name of the table (`DnsEvents`). |

> Plus the billing/system columns `_BilledSize` (real), `_IsBillable` (string), `_ResourceId` (string), `_SubscriptionId` (string). **Total: 27 columns** per the reference page. No column has been invented; this table has **no `dynamic` columns** — `IPAddresses` is a comma-joined **string**, not an array.

## Key columns for detection & hunting
- **Identity:** n/a directly — the legacy `DnsEvents` schema does **not** carry a user/UPN or process. Attribute activity by mapping `ClientIP` to a host/user via `DeviceLogonEvents` / `SigninLogs` / DHCP. (The newer `ASimDnsActivityLog` AMA path can add user/process; this table cannot.)
- **Host / device:** `Computer` is the **DNS server** that answered (not the client). The querying endpoint is identified only by `ClientIP`.
- **Network:** `ClientIP` (requester) and `IPAddresses` (resolved answer string). `MaliciousIP` flags a TI-matched address. Geo via `RemoteIPCountry` / `RemoteIPLatitude` / `RemoteIPLongitude`.
- **Outcome / result:** `ResultCode` — an **int** where `0` = success and non-zero = failure (e.g. `9003` NXDOMAIN). `Result` is the parallel **string** label. Use `ResultCode != 0` for failed resolutions.
- **Timestamps:** `TimeGenerated` (there is no separate event-time column in this table).
- **Join keys (to other tables):** `ClientIP` (→ `DeviceLogonEvents.RemoteIP` / `DeviceNetworkEvents.LocalIP` / `SigninLogs.IPAddress` to attribute the client), `Name` (→ proxy/`DeviceNetworkEvents.RemoteUrl` and threat-intel domain indicators), `Computer` (→ `SecurityEvent` / `Heartbeat` for the DNS server), `IPAddresses` / `MaliciousIP` (→ network connection logs and TI).

## ⚠️ Schema gotchas
- **`Computer` is the DNS SERVER, not the client.** A query from FIN-WS-07 logged by DC01 shows `Computer == "DC01"` and `ClientIP ==` FIN-WS-07's address. Pivoting on `Computer` to find "the infected host" is wrong — pivot on `ClientIP`.
- **`ResultCode` is an INT (`0` = success); `Result` is the STRING twin.** Filter failures with `ResultCode != 0`, not by a string. NXDOMAIN surfaces as `ResultCode == 9003` (Windows DNS) with `Result == "NXDOMAIN"`.
- **`IPAddresses` is a comma-joined STRING, not a `dynamic`/array.** To count or match answers use `split(IPAddresses, ",")` or `has`/`contains` — `IPAddresses[0]` will not work as array indexing.
- **No user or process on this table.** Unlike `ASimDnsActivityLog` (AMA) or endpoint DNS, legacy `DnsEvents` has no UPN/account/process columns. Attribution requires a `ClientIP` join.
- **TI columns are empty unless DNS TI matching is enabled.** `MaliciousIP`, `IndicatorThreatType`, and `Confidence` populate only when the workspace has threat-intelligence enrichment on DNS — do not assume their absence means "clean", and do not build a detection that *requires* them.

## 🧪 Sample data
[`DnsEvents_sample.csv`](DnsEvents_sample.csv) — 34 rows. The rows tell the **Operation Quiet Ledger** C2/beaconing step (~09:15): `FIN-WS-07`'s `ClientIP` (`10.20.7.31`) makes **repeated, periodic lookups of `badupdate-cdn.com`** plus **long random DGA-style subdomains** (mixed `A`/`TXT`) with intermittent **NXDOMAIN** (`ResultCode 9003`) — some TI-flagged via `MaliciousIP` / `IndicatorThreatType == "C2"` — all answered by `DC01`, against a backdrop of **high-volume benign resolutions** (`microsoft.com`, `contoso.com`, `windowsupdate`, `outlook.office365.com`) from other clients.
The sample uses this curated subset of **real** columns: `TimeGenerated`, `Computer`, `ClientIP`, `Name`, `QueryType`, `IPAddresses`, `Result`, `ResultCode`, `SubType`, `EventId`, `MaliciousIP`, `IndicatorThreatType`, `Confidence`, `Severity`. This is the **C2 DNS step (~09:15 beaconing / DGA from FIN-WS-07 via DC01)** of the cross-table attack scenario.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · Rare domain with a high NXDOMAIN ratio — DGA / failing C2 — [T1568.002](https://attack.mitre.org/techniques/T1568/002/)
**Hypothesis:** A client that generates many distinct second-level domains with a high proportion of **NXDOMAIN** failures is exhibiting Domain Generation Algorithm behaviour (most generated domains aren't registered yet).
```kusto
DnsEvents
| where SubType == "LookupQuery"
| extend Registered2LD = strcat(tostring(split(Name, ".")[-2]), ".", tostring(split(Name, ".")[-1]))
| summarize Total = count(),
            NxDomain = countif(ResultCode == 9003),
            DistinctNames = dcount(Name)
        by ClientIP, Registered2LD
| extend NxRatio = round(todouble(NxDomain) / Total, 2)
| where Total >= 3 and NxRatio >= 0.4
| sort by NxRatio desc, DistinctNames desc
```
**Triage:** True positive = one `ClientIP` (e.g. FIN-WS-07 `10.20.7.31`) fanning out many random subdomains under `badupdate-cdn.com` with NXDOMAIN ≥ 40% (DGA). Benign = a CDN/anti-spam/typo cluster — verify the parent domain reputation and whether the labels are human-readable vs random.

### H2 · Suspicious TXT-record queries — DNS tunnelling / C2 channel — [T1071.004](https://attack.mitre.org/techniques/T1071/004/)
**Hypothesis:** TXT lookups are rare in normal user traffic; a client issuing repeated TXT queries — especially for long or random labels on one domain — suggests a DNS-tunnelling / C2 data channel.
```kusto
DnsEvents
| where SubType == "LookupQuery" and QueryType == "TXT"
| extend NameLength = strlen(Name)
| summarize TxtQueries = count(),
            DistinctNames = dcount(Name),
            MaxNameLength = max(NameLength),
            FirstSeen = min(TimeGenerated), LastSeen = max(TimeGenerated)
        by ClientIP
| where TxtQueries >= 3
| sort by TxtQueries desc, MaxNameLength desc
```
**Triage:** True positive = a workstation `ClientIP` issuing many long TXT queries to `badupdate-cdn.com` (encoded payload). Benign = mail servers doing SPF/DKIM/DMARC TXT lookups for known mail domains — exclude your mail relays and confirm the queried name isn't a legitimate mail/SaaS domain.

### H3 · Threat-intelligence-matched DNS resolution — known-bad domain/IP — [T1071.001](https://attack.mitre.org/techniques/T1071/001/)
**Hypothesis:** Any lookup whose answer was flagged by threat intelligence (`MaliciousIP` populated, or `IndicatorThreatType` set) identifies a client communicating with known-malicious infrastructure.
```kusto
DnsEvents
| where SubType == "LookupQuery"
| where isnotempty(MaliciousIP) or isnotempty(IndicatorThreatType)
| project TimeGenerated, ClientIP, Name, QueryType, IPAddresses, MaliciousIP, IndicatorThreatType, Confidence
| summarize Hits = count(), DistinctNames = dcount(Name), Names = make_set(Name, 10)
        by ClientIP, IndicatorThreatType
| sort by Hits desc
```
**Triage:** True positive = a client repeatedly resolving a `C2`/`Botnet`-typed indicator (FIN-WS-07 → `badupdate-cdn.com`). Benign = a stale/low-confidence indicator or a sinkholed domain — check `Confidence` and whether the IP is a known sinkhole before escalating.

### H4 · Beaconing — periodic lookups of one domain — [T1071.004](https://attack.mitre.org/techniques/T1071/004/)
**Hypothesis:** Regular, repeated resolution of the same domain from one client at a steady cadence is classic C2 beaconing.
```kusto
DnsEvents
| where SubType == "LookupQuery"
| summarize Lookups = count(),
            FirstSeen = min(TimeGenerated), LastSeen = max(TimeGenerated),
            WindowMinutes = datetime_diff('minute', max(TimeGenerated), min(TimeGenerated))
        by ClientIP, Name
| where Lookups >= 4 and WindowMinutes between (1 .. 120)
| extend AvgIntervalMin = round(todouble(WindowMinutes) / Lookups, 1)
| sort by Lookups desc
```
**Triage:** True positive = `10.20.7.31` resolving `badupdate-cdn.com` many times over the morning at a near-constant interval. Benign = telemetry/update endpoints (`windowsupdate`, `outlook.office365.com`) that also poll regularly — allow-list known SaaS/update FQDNs.

## 🔗 Correlates with
- **DeviceLogonEvents / DeviceNetworkEvents** on `ClientIP` → `RemoteIP`/`LocalIP` + `Computer`/`DeviceName` — attribute the querying `ClientIP` to FIN-WS-07 and confirm the actual outbound C2 connection to the resolved IP.
- **SecurityEvent** on `Computer` (the DNS server) and on `ClientIP`→host — corroborate process/network activity (4688) on the host that generated the lookups.
- **SigninLogs** on `ClientIP` → `IPAddress` — tie the client's resolutions to the compromised identity (`alexw`) and the earlier risky sign-in.
- **ThreatIntelligenceIndicator** on `Name`/`MaliciousIP` → `DomainName`/`NetworkIP` — confirm the matched indicator's source, validity window, and confidence.

## 📚 References
- [DnsEvents — Azure Monitor reference](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/dnsevents)
- [Queries for the DnsEvents table (sample KQL)](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/queries/dnsevents)
- [Windows DNS Events via AMA connector — fields & normalization](https://learn.microsoft.com/en-us/azure/sentinel/dns-ama-fields)
- [ASIM DNS normalization schema reference](https://learn.microsoft.com/en-us/azure/sentinel/normalization-schema-dns)
