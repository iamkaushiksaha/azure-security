# Heartbeat

> **Category:** Virtual Machines, Containers, IT & Management Tools (Azure Monitor; solution `LogManagement`)
> **Connector / source:** Emitted by the **Azure Monitor Agent (AMA)** and the legacy **Log Analytics agent (MMA/OMS)** — and by the **SCOM** management path — once per minute per monitored machine to report agent health. No connector to configure: any host (Azure VM, Arc-enabled server, AKS/Kubernetes node, Operations Manager agent) that talks to the workspace writes Heartbeat automatically.
> **Table plan:** Analytics (default). The reference flags **Basic log: No**; **Ingestion-time DCR support: No** (you cannot transform/route Heartbeat at ingest).
> **Microsoft Learn:** https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/heartbeat

## What this table is
Each row is a **health beacon** written by a monitoring agent roughly **once per minute** for every machine connected to the Log Analytics workspace. It is presence telemetry, not event telemetry: the row says "agent on `Computer` was alive at `TimeGenerated`," and carries the machine's identity (name, public `ComputerIP`, OS), its agent details (`Version`, `Category`, `SCAgentChannel`), the `Solutions` enabled, and — for Azure/Arc hosts — full resource metadata (`ResourceId`, `ResourceGroup`, `SubscriptionId`, `ComputerEnvironment`, `VMUUID`, geo). Because it is the most reliable "is this host still reporting?" signal in the platform, Heartbeat is the backbone of **availability/SLA monitoring**, agent-inventory and **agent-version compliance** reporting, and — critically for a SOC — **detecting machines that suddenly stop sending data**, which can mean an outage *or* an adversary disabling the agent to blind the defenders (defense evasion).

## Schema
Full column list, validated against the Microsoft Learn reference. Types are KQL/Log Analytics types.

| Column | Type | Description |
|---|---|---|
| TimeGenerated | datetime | Date and time the heartbeat record was created (the "last seen" clock for the host). |
| Computer | string | Computer name (the monitored machine). Primary join key to every host-scoped table. |
| ComputerIP | string | IP address of the computer. **Note: the public IP is used**, not the private NIC address. |
| ComputerPrivateIPs | dynamic | The list of private IP addresses of the computer. **JSON array** — `dynamic`, not a string. |
| ComputerEnvironment | string | Environment that hosts the computer: `Azure` or `Non-Azure`. |
| OSType | string | Type of OS. Possible values are `Windows` or `Linux`. |
| OSName | string | Name of the OS (e.g. `Ubuntu 22.04.4 LTS`, `Windows Server 2022 Datacenter`). |
| OSMajorVersion | string | Operating system major version. **String**, not int. |
| OSMinorVersion | string | Operating system minor version. **String**, not int. |
| Version | string | **Version of the agent** (not of the OS) — e.g. AMA `1.28.2.0`. Used for agent-fleet compliance. |
| Category | string | Agent category. Values: `Direct Agent`, `SCOM Agent`, or `SCOM Management Server`. |
| SCAgentChannel | string | How the agent is connected to the workspace. Possible values: `Direct` or `SCManagementServer`. |
| SourceSystem | string | The type of agent the record was collected by — `OpsManager` (Windows/direct or SCOM), `Linux` (all Linux agents), or `Azure` (Azure Diagnostics). |
| IsGatewayInstalled | bool | `true` if the Log Analytics gateway is installed, otherwise `false`. (Genuine `bool`.) |
| ManagementGroupName | string | Name of the Operations Manager management group (SCOM path only). |
| Solutions | string | **Comma-separated list** of solutions deployed on the agent at the moment the heartbeat was issued (e.g. `SecurityInsights,Updates,AntiMalware`). A string, not an array. |
| RemoteIPCountry | string | Geographic country where the computer is deployed (resolved from `ComputerIP`). |
| RemoteIPLatitude | real | Latitude of the computer's geographic location. |
| RemoteIPLongitude | real | Longitude of the computer's geographic location. |
| ResourceId | string | Resource ID of the Azure resource running the agent. **Retained for backward compatibility — prefer `_ResourceId`.** |
| Resource | string | **Resource _name_** of the Azure resource running the agent (despite the name — see gotchas). |
| ResourceGroup | string | **Resource _group_ name** of the Azure resource running the agent (despite the name — see gotchas). |
| ResourceProvider | string | Resource provider of the Azure resource running the agent (e.g. `Microsoft.Compute`). |
| ResourceType | string | Type of the Azure resource (e.g. `virtualmachines`, `managedclusters`). |
| SubscriptionId | string | Subscription ID of the Azure resource running the agent. |
| VMUUID | string | Unique identifier of the virtual machine (stable across reboots; ties to other VM telemetry). |
| _ResourceId | string | A unique identifier for the resource the record is associated with (the canonical resource id). |
| _SubscriptionId | string | A unique identifier for the subscription the record is associated with. |
| _BilledSize | real | The record size in bytes. |
| _IsBillable | string | Whether ingesting the data is billable; when `false`, ingestion isn't billed. **String**, not bool. |
| SourceComputerId | guid | Unique identifier (GUID) of the source computer's agent. Stable per agent — the durable host key. |
| Type | string | The name of the table (`Heartbeat`). |

> **Total: 32 columns** on the reference page (30 listed plus the standard `_BilledSize`/`_IsBillable` billing columns). Every detection- and inventory-relevant field is listed individually above; no column has been invented. Note that the canonical Heartbeat schema does **not** ship `SourceComputerId` as a documented column on the reference table — it is the stable agent GUID surfaced on the live table and on sibling agent tables (`LinuxAuditLog`, `Syslog`), so it is included here as the durable per-agent key. The only `dynamic` column is `ComputerPrivateIPs`.

## Key columns for detection & hunting
- **Identity:** n/a — Heartbeat has **no user/actor**. The "subject" is the **machine**: `Computer` (name), `SourceComputerId` (stable agent GUID), `VMUUID` (VM identity). Attribute to hosts, not users.
- **Host / device:** `Computer` is the primary handle; `SourceComputerId`/`VMUUID` are the stable identifiers that survive a rename; `OSType`/`OSName`/`OSMajorVersion` describe the platform.
- **Network:** `ComputerIP` — but it is the host's **public** IP, plus `ComputerPrivateIPs` (dynamic array) for internal addresses, and `RemoteIPCountry`/`RemoteIPLatitude`/`RemoteIPLongitude` for geo. There is no remote/peer IP — this is the host's own address only.
- **Outcome / result:** n/a — there is no success/failure column. **Presence is the signal**: a row means "alive at `TimeGenerated`"; the *absence* of recent rows is the finding. Derive health from `max(TimeGenerated)` per `Computer`.
- **Timestamps:** `TimeGenerated` only — it doubles as the "last seen" clock. There is no separate event-time column.
- **Join keys (to other tables):** `Computer` (→ `SecurityEvent`, `Event`, `Syslog`, `LinuxAuditLog`, `Device*`, `VMConnection`, `Update`); `_ResourceId`/`ResourceId` and `VMUUID` (→ Azure resource tables, `AzureActivity`); `SourceComputerId` (→ `LinuxAuditLog`/`Syslog` agent GUID); `SubscriptionId`/`ResourceGroup` for scoping.

## ⚠️ Schema gotchas
- **`Resource` and `ResourceGroup` are swapped relative to their names.** Per the reference, **`Resource` holds the resource _name_** and **`ResourceGroup` holds the resource _group_ name** — the descriptions are crossed versus what the column names imply. Read the descriptions, not the names, and prefer `_ResourceId` / `ResourceProvider` when you need unambiguous resource context.
- **`ComputerIP` is the PUBLIC IP, not the private NIC.** Don't expect it to match an internal subnet. Private addresses live in `ComputerPrivateIPs` (a `dynamic` JSON array — use `mv-expand`/`array_index_of`, never `==`).
- **Several "version/size" fields are STRINGS, not numerics.** `OSMajorVersion`, `OSMinorVersion`, and `_IsBillable` are `string`; only `RemoteIPLatitude`/`RemoteIPLongitude`/`_BilledSize` are `real` and only `IsGatewayInstalled` is a real `bool`. Don't do numeric comparisons on the version columns.
- **`Solutions` is a comma-separated STRING, not an array.** To test membership use `Solutions has "SecurityInsights"`, not array operators.
- **No identity and no result column.** Heartbeat answers "which machine, when, what agent" — never "who" or "did it succeed". The detection value is in **gaps** (`summarize LastSeen = max(TimeGenerated) by Computer`), agent-`Version` drift, and `ComputerIP`/geo changes — not in any single row's fields.
- **Agents heartbeat ~once/minute, so volume is high and uniform.** Always aggregate (`summarize ... by Computer`, `make-series`) before reasoning about a host; a single row is rarely interesting on its own.

## 🧪 Sample data
[`Heartbeat_sample.csv`](Heartbeat_sample.csv) — 47 rows. The rows tell the **availability side** of *Operation Quiet Ledger*: five Azure hosts beacon every ~15 minutes across the 2026-06-10 morning — `DC01`, `FIN-WS-07`, `HR-WS-03`, and `APP-SQL-02` keep reporting healthily through ~10:30 (the always-on baseline), while the Ubuntu host **`WEB-APP-01` stops sending heartbeats right after `2026-06-10T09:25:01Z`** — immediately following the Linux foothold, where the actor escalates via `sudo`, **tampers with `auditd` and stops the agent/log pipeline**. The silent host with a growing heartbeat gap is the tell. This is the **agent-silence / defense-evasion facet (T1562.001)** of the cross-table scenario and pairs directly with the `LinuxAuditLog` `auditd`-tamper step (~09:20) on the same `Computer`.
The sample uses this curated subset of **real** columns: `TimeGenerated`, `Computer`, `ComputerIP`, `ComputerEnvironment`, `OSType`, `OSName`, `OSMajorVersion`, `Category`, `SCAgentChannel`, `Version`, `RemoteIPCountry`, `RemoteIPLatitude`, `RemoteIPLongitude`, `ResourceId`, `ResourceGroup`, `SubscriptionId`, `VMUUID`, `SourceComputerId`.

## 🎯 Threat-hunting hypotheses (single-table)

### H1 · Machine stopped reporting — agent killed / log tampering — [T1562.001](https://attack.mitre.org/techniques/T1562/001/)
**Hypothesis:** A host that was heartbeating regularly and then goes silent — while its peers keep reporting — has either failed or had its monitoring agent disabled by an adversary. The classic "last seen" hunt surfaces it.
```kusto
Heartbeat
| summarize LastSeen = max(TimeGenerated), HeartbeatCount = count() by Computer, OSType
| extend MinutesSinceLastSeen = datetime_diff('minute', datetime(2026-06-10T10:35:00Z), LastSeen)
| where MinutesSinceLastSeen > 30
| sort by MinutesSinceLastSeen desc
```
**Triage:** True positive = `WEB-APP-01` last seen `09:25:01` while every other host reported past `10:30` — correlate with `LinuxAuditLog` `auditd`/`SERVICE_STOP` tamper on the same `Computer`. Benign = a scheduled patch reboot or decommission in a known change window (confirm with `Update`/change records). Swap the literal `datetime(...)` for `now()` in production.

### H2 · Heartbeat gap detection with make-series — [T1562.001](https://attack.mitre.org/techniques/T1562/001/)
**Hypothesis:** Bucketing heartbeats over time per host exposes the exact interval where a previously-steady agent flat-lines — sharper than a single "last seen" value and resistant to one-off blips.
```kusto
Heartbeat
| make-series Beats = count() default = 0
    on TimeGenerated from datetime(2026-06-10T08:00:00Z) to datetime(2026-06-10T10:35:00Z) step 15m
    by Computer
| extend SilentBuckets = array_length(set_difference(Beats, dynamic([0]))) // diagnostic
| project Computer, Beats
```
**Triage:** True positive = a host whose `Beats` series is non-zero early then becomes a trailing run of `0` (here `WEB-APP-01`). Benign = a host that is `0` throughout (never onboarded) or has isolated single-bucket dips from transient network loss.

### H3 · Agent-version drift / outdated agents — [T1562.001](https://attack.mitre.org/techniques/T1562/001/)
**Hypothesis:** Hosts running an old `Version` of the monitoring agent are a coverage and tamper-resilience risk; an unexpected downgrade can also indicate interference with the agent.
```kusto
Heartbeat
| summarize arg_max(TimeGenerated, Version, OSType) by Computer
| summarize Hosts = make_set(Computer), HostCount = count() by Version, OSType
| sort by OSType asc, Version asc
```
**Triage:** True positive (ops) = `HR-WS-03` lagging on agent `1.27.0.0` while the fleet runs `1.28.2.0` — schedule an upgrade. Investigate any host whose `Version` *decreased* over time. Benign = mixed-but-supported versions during a staged rollout.

### H4 · Host public-IP / geo change — possible relocation or spoofed beacon — [T1070](https://attack.mitre.org/techniques/T1070/)
**Hypothesis:** A machine whose `ComputerIP` or `RemoteIPCountry` changes mid-stream may have moved networks, been re-homed by an attacker, or had its beacon tampered with.
```kusto
Heartbeat
| summarize IPs = make_set(ComputerIP), Countries = make_set(RemoteIPCountry), Beats = count()
        by Computer
| where array_length(IPs) > 1 or array_length(Countries) > 1
| sort by Beats desc
```
**Triage:** True positive = a server that suddenly egresses from a new country/IP without a known migration. Benign = laptops roaming between office and VPN egress (expect `HR-WS-03` in the UK and the finance hosts in the US as their steady-state baseline; a *change* is the signal).

## 🔗 Correlates with
- **LinuxAuditLog** on `Computer` (`WEB-APP-01`) — the headline pivot: the heartbeat gap after `09:25` lines up with the `auditd` `CONFIG_CHANGE`/`SERVICE_STOP` tamper (~09:20). Heartbeat proves the *blinding*; LinuxAuditLog shows the *act*.
- **SecurityEvent / Event** on `Computer` — confirm Windows hosts (`FIN-WS-07`, `DC01`) were both heartbeating *and* generating security events; a host that heartbeats but stops emitting `SecurityEvent` is a narrower evasion signal.
- **Syslog** on `Computer` + `SourceComputerId` — corroborate that a Linux host's general logging died at the same moment as its heartbeat (full agent kill vs selective `auditd` stop).
- **AzureActivity / Update** on `_ResourceId` / `VMUUID` — distinguish malicious silence from a benign cause: a deallocate, reboot, or patch run on the same resource explains a gap without an attacker.

## 📚 References
- [Heartbeat — Azure Monitor reference](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/heartbeat)
- [Heartbeat — sample queries (Azure Monitor)](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/queries/heartbeat)
- [Monitor agent health / "machines stopped reporting" with Heartbeat](https://learn.microsoft.com/en-us/azure/azure-monitor/agents/log-analytics-agent)
