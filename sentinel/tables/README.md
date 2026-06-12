<div align="center">

# 🗂️ Microsoft Sentinel Table Library

**Schema-accurate reference + ready-to-ingest sample logs for 21 Log Analytics / Defender XDR tables — woven into one correlated attack scenario you can hunt, triage, and test detections against.**

![Microsoft Sentinel](https://img.shields.io/badge/Microsoft-Sentinel-0078D4?logo=microsoftazure&logoColor=white)
![Tables](https://img.shields.io/badge/Tables-21-512BD4)
![Schema validated](https://img.shields.io/badge/Schema-validated%20vs%20MS%20Learn-2EA043)
![MITRE ATT&CK](https://img.shields.io/badge/Mapped-MITRE%20ATT%26CK-red)
![Sample logs](https://img.shields.io/badge/Sample%20logs-included-success)

</div>

---

Real Sentinel environments rarely have every table populated, so analysts can't practise hunts, learn an unfamiliar schema, or **test an analytic rule before shipping it**. This library fixes that. Each table gets its own folder with:

- a **plain-English description** of what the table is and when rows appear,
- the **full schema** (every column + type) validated against the Microsoft Learn table reference,
- the **key columns for detection**, the **schema gotchas** that silently break queries,
- **single-table, MITRE-mapped hunting hypotheses** with runnable KQL, and
- a **schema-true sample CSV** you can ingest.

Every sample uses the **same cast of users, IPs, and hosts**, so the 21 standalone files also act as **one correlated dataset** — see the [Operation Quiet Ledger scenario](scenarios/operation-quiet-ledger/README.md) for the cross-table joins.

> [!NOTE]
> **Schema-accurate, not schema-exhaustive.** Each table doc lists every column from Microsoft Learn, but each sample CSV ships a *curated subset* of the most detection-relevant real columns (10–22 of them) so the data stays readable and runnable. Column names and types are always exact.

## 📁 The tables

### 🔐 Identity & Microsoft 365
| Table | What it captures | Sample story | Key MITRE |
|---|---|---|---|
| [SigninLogs](SigninLogs/README.md) | Entra ID interactive sign-ins | Risky success from a Tor IP after a brute-force burst | T1110 · T1078 |
| [OfficeActivity](OfficeActivity/README.md) | M365 unified audit (Exchange/SharePoint/Teams) | Malicious inbox rule + mass file download/share | T1114.003 · T1567.002 |
| [EmailEvents](EmailEvents/README.md) | Defender for O365 email + verdicts | Lookalike-domain phish delivered (ZAP miss) | T1566.001 · T1566.002 |

### 💻 Endpoint (Microsoft Defender for Endpoint)
| Table | What it captures | Sample story | Key MITRE |
|---|---|---|---|
| [DeviceLogonEvents](DeviceLogonEvents/README.md) | Device authentications | RDP onto FIN-WS-07, then a DC01 failure burst | T1021.001 · T1110 |
| [DeviceProcessEvents → DeviceEvents](DeviceEvents/README.md) | ASR / AMSI / misc device security events | ASR audit→block, AMSI catch, LOLBins | T1059 · T1218 |
| [DeviceFileEvents](DeviceFileEvents/README.md) | File create/modify/rename | Payload drop, renamed cred-dumper, staged ZIP | T1105 · T1560.001 · T1003 |

### 🪟 Windows host logs
| Table | What it captures | Sample story | Key MITRE |
|---|---|---|---|
| [SecurityEvent](SecurityEvent/README.md) | Windows Security log (4624/4625/4688/4720…) | Spray → logon → special privs → account created | T1110.003 · T1136.001 |
| [Event](Event/README.md) | Windows System & Application logs | Malicious 7045 service install; Defender 1116 | T1543.003 · T1489 |

### 🐧 Linux & cross-platform
| Table | What it captures | Sample story | Key MITRE |
|---|---|---|---|
| [Syslog](Syslog/README.md) | Linux syslog (free-text) | SSH brute force → accepted → sudo to root | T1110 · T1548.003 |
| [LinuxAuditLog](LinuxAuditLog/README.md) | Linux auditd records | /etc/shadow read, payload run, auditd tamper | T1003.008 · T1562.001 |
| [ASimAgentEventLogs](ASimAgentEventLogs/README.md) | **ASIM AI/LLM agent** telemetry (model/tool/tokens) | AI agent driven to call storage/KeyVault tools | T1059 · T1565.001 |

### 🌐 DNS & network
| Table | What it captures | Sample story | Key MITRE |
|---|---|---|---|
| [DnsEvents](DnsEvents/README.md) | Windows DNS query/analytic events | C2 beacon + DGA subdomains + NXDOMAIN spikes | T1568.002 · T1071.004 |
| [DnsAuditEvents](DnsAuditEvents/README.md) | Windows DNS **audit** (zone/record changes) | Rogue records + malicious forwarder planted | T1565 · T1556 |

### ☁️ Azure control plane & resources
| Table | What it captures | Sample story | Key MITRE |
|---|---|---|---|
| [AzureActivity](AzureActivity/README.md) | ARM subscription activity log | roleAssignments/write + listKeys + NSG open | T1098.003 · T1552.005 |
| [AzureDiagnostics](AzureDiagnostics/README.md) | Multi-resource diagnostics (Key Vault, NSG…) | Key Vault secret/key harvest after a role grant | T1555.006 · T1078.004 |
| [StorageBlobLogs](StorageBlobLogs/README.md) | Storage blob data-plane | AccountKey + Anonymous exfil of finance blobs | T1567 · T1530 |

### ⚙️ Kubernetes (AKS)
| Table | What it captures | Sample story | Key MITRE |
|---|---|---|---|
| [AKSAudit](AKSAudit/README.md) | Full Kubernetes API audit | Secret enumeration + `pods/exec` recon | T1609 · T1552.007 |
| [AKSAuditAdmin](AKSAuditAdmin/README.md) | API audit, **admin subset** (no get/list/watch) | clusterrolebinding→cluster-admin, logging deleted | T1098 · T1562.001 |

### 📊 Sentinel alerts & operations
| Table | What it captures | Sample story | Key MITRE |
|---|---|---|---|
| [Alert](Alert/README.md) | Azure Monitor alerts (legacy log-search/SCOM) | Infra alerts fire across the incident window | *(triage corroboration)* |
| [Usage](Usage/README.md) | Per-table ingestion metering | Ingestion spike; Syslog drops to 0 (source killed) | T1562.008 |
| [Heartbeat](Heartbeat/README.md) | Agent health beacon | WEB-APP-01 goes silent mid-attack | T1562.001 |

## 🎯 The correlated scenario — "Operation Quiet Ledger"

The sample data isn't 21 disconnected demos — it's **one intrusion** seen from 21 angles, all on **2026-06-10**: an emailed phish compromises a finance analyst (`alexw`), who is driven from a Tor IP onto `FIN-WS-07`, laterally to `DC01`, then pivots into Azure to escalate privilege, harvest secrets, and exfiltrate finance data from blob storage and AKS — with a parallel Linux foothold on `WEB-APP-01`.

➡️ **[Read the full scenario, kill-chain, and cross-table join queries →](scenarios/operation-quiet-ledger/README.md)**

It's built for four jobs:
1. **Learn a table** — open its folder, read the schema, run its single-table hunts.
2. **Practise correlation** — run the multi-table joins that reconstruct the intrusion.
3. **Rehearse triage** — start from one alert and pivot to full blast radius.
4. **Test an analytic rule** — ingest the samples and confirm your scheduled rule fires (and doesn't over-fire on the benign noise mixed into every file).

## 🔑 Shared cast & indicators (the correlation spine)

| Type | Value | Role |
|---|---|---|
| User | `alexw@contoso.com` | Compromised finance analyst (the through-line) |
| User | `priya.menon@contoso.com` | Phished first (delivery) |
| User | `svc-backup@contoso.com` | Service principal abused for Azure persistence |
| Users (benign) | `meganb@`, `jamest@`, `dvora@`, `itadmin@` | Noise / legitimate admins |
| Attacker IP | `185.220.101.2` (NL) · `91.219.236.18` | Primary / secondary |
| Domains | `login-contoso-sso.com` · `badupdate-cdn.com` | Phish / C2 |
| Hosts | `FIN-WS-07` · `DC01` · `WEB-APP-01` · `aks-prod-01` | Workstation / DC / Linux / cluster |
| Azure | `stcontosofin` · `kv-contoso-prod` · `rg-finance-prod` | Storage / Key Vault / resource group |

## 🚀 How to use this library

**Just reading / learning?** Browse a table's folder — the README is self-contained.

**Want to run the queries?** Ingest the sample CSVs one of two ways:

- **Azure Data Explorer free cluster** (no Azure subscription) — [https://aka.ms/kustofree](https://aka.ms/kustofree), then *Get data → Local file* per table, or use the generator in the [Sentinel Hunter skill](../../.claude/skills/azure-sentinel-hunter/) to emit `.create table` + ingest commands.
- **Log Analytics / Sentinel** — paste a CSV into a `datatable()` and save it as a function named after the table (the [KQL Mastery Path Stage 00](../kql/00-setup/README.md) shows the exact pattern, including a zero-permission `let` variant).

> The companion **[KQL Mastery Path](../kql/README.md)** teaches the language from scratch; this library is the **data + schema reference** those skills run against.

## 🧱 Principles

- **Schema-true or it doesn't ship.** Every column name and type is validated against the Microsoft Learn table reference; gotchas (string `ResultType`, dynamic `InitiatedBy`, legacy `Alert`, the `_s/_d` suffix convention…) are called out per table.
- **Signal *and* noise.** Every sample mixes malicious rows with benign activity, so a detection that only works because "everything is evil" will visibly over-fire here.
- **MITRE-anchored.** Hunts cite real ATT&CK technique IDs; the scenario ships an [ATT&CK Navigator layer](scenarios/operation-quiet-ledger/mitre-navigator-layer.json).
- **Tunable, not gospel.** Thresholds are realistic starting points to adapt to your baseline.

---

<div align="center">

*Part of the [azure-security](../../README.md) repository · pairs with the [KQL Mastery Path](../kql/README.md) and the [Azure Sentinel Hunter skill](../../.claude/skills/azure-sentinel-hunter/).*

</div>
