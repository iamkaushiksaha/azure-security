# Azure Security

Hands-on Azure security work by **Kaushik Saha**, free to use. It starts with **Microsoft Sentinel** and **KQL**
(Kusto Query Language): a KQL course you can run with an empty workspace, a library of 27 Sentinel and Defender XDR
tables with sample logs, a correlated attack scenario, an example analytic rule, and a reusable threat-hunting skill.
More areas of Azure security follow (see [Coming next](#coming-next)).

> **Learn KQL interactively → [verikql.kaushiksaha.com/learn](https://verikql.kaushiksaha.com/learn)**
>
> The **KQL Mastery Path** on VeriKQL takes you from your first query to closing a case, in six levels. Every
> query on the site is checked with Microsoft's own KQL parser against the real table schemas. This repository holds
> the source material behind the site's reference course and table library.

## Start here

1. **Learn the language:** the [KQL reference course](sentinel/kql/README.md). Stage 00 gives you practice data
   in about five minutes, even with an empty workspace or no Azure subscription.
2. **Learn the data:** the [table library](sentinel/tables/README.md): what each table holds, its schema and its
   traps.
3. **Hunt an incident:** [Operation Quiet Ledger](sentinel/tables/scenarios/operation-quiet-ledger/README.md),
   one attack traced across the tables.
4. **Ship a detection:** the [example analytic rule](sentinel/analytic-rules/README.md), with its hypothesis,
   tuning notes and a test against the scenario's data.

## What's here

| | What it is | Start with |
|---|---|---|
| **KQL reference course** | Five stages from setup to threat hunting, plus a cheat sheet, schema gotchas and Microsoft links. Stage 00 seeds a dataset, so you can practise with no logs flowing | [`sentinel/kql/`](sentinel/kql/README.md) |
| **Sentinel table library** | 27 Log Analytics and Defender XDR tables: what each holds, its full schema, gotchas, sample logs and MITRE ATT&CK-mapped hunts | [`sentinel/tables/`](sentinel/tables/README.md) |
| **Attack scenario: Operation Quiet Ledger** | One correlated incident across the tables, for triage practice and for testing analytic rules before you ship them | [`sentinel/tables/scenarios/operation-quiet-ledger/`](sentinel/tables/scenarios/operation-quiet-ledger/README.md) |
| **Example analytic rule** | Storage key theft followed by blob exfiltration, as KQL and as a deployable rule (YAML) | [`sentinel/analytic-rules/`](sentinel/analytic-rules/README.md) |
| **Azure Data Explorer labs** | Load several Sentinel-style tables into a free ADX cluster and practise joins, with small teaching CSVs | [`sentinel/labs/`](sentinel/labs/README.md), [`sentinel/sampledata/`](sentinel/sampledata/README.md) |
| **Azure Sentinel Hunter skill** | A reusable skill for AI assistants: KQL authoring, detection engineering and threat hunting, with references, scripts and rule templates | [`.claude/skills/azure-sentinel-hunter/`](.claude/skills/azure-sentinel-hunter/SKILL.md) |

All sample data is synthetic (Contoso and Fabrikam users, placeholder subscription IDs); nothing comes from a real
tenant. Some IP addresses belong to real public ranges for realism, so don't block them on this data alone.

**Checked on 2026-11-08:** every query compiles and binds against the Microsoft Sentinel and Defender XDR table
schemas with Microsoft's KQL parser (via VeriKQL), and every ATT&CK technique ID is current in ATT&CK v20.

## Coming next

Each area is added when its material is ready and checked, rather than as an empty folder.

- **Microsoft Defender for Cloud:** posture (secure score and recommendations), workload protection plans, and
  querying its alerts and recommendations with KQL and Azure Resource Graph.
- **Microsoft Entra ID security:** sign-in and audit hunting, Conditional Access, and identity incident response
  (disabling accounts, revoking sessions, least-privilege Microsoft Graph permissions for automation).
- **SOAR with Logic Apps:** Microsoft Sentinel playbooks and automation rules, starting with incident hand-off to
  ServiceNow.
- **Operational scripts:** PowerShell, Python and Azure CLI for Sentinel and Azure security operations, such as
  exporting Content Hub rule templates and auditing Azure Container Registry policies.

## Check your own KQL

[**VeriKQL**](https://verikql.kaushiksaha.com) checks KQL for Microsoft Sentinel and Defender XDR with Microsoft's
own parser against a pinned table-schema bundle, and returns a proof record. It never runs your query and never sees
your logs. Use it on the site, or connect it to Claude or ChatGPT as an MCP server.

## Writing new material

New pages follow the [style guide](docs/style-guide.md) and start from the
[page template](docs/templates/page-template.md): every query runnable, checked with Microsoft's parser, and mapped
to the current ATT&CK release.

## Licence

- **Written material** (the course, the table library, the scenario, the labs and the other Markdown documents) is
  licensed under [Creative Commons Attribution 4.0 International](LICENSE) (CC BY 4.0). You may share and adapt it,
  including commercially, if you credit **Kaushik Saha** and link to this repository.
- **Code** (KQL queries in `.kql` files, rule definitions, scripts and sample data) is licensed under the
  [MIT License](LICENSE-CODE).

Microsoft, Microsoft Sentinel, Microsoft Defender and Azure are trademarks of the Microsoft group of companies. This
repository is independent: it is not affiliated with, sponsored or endorsed by Microsoft.
