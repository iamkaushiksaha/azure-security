# Azure Security: KQL and Microsoft Sentinel, hands-on

Free learning and detection-engineering material for **Microsoft Sentinel** and **KQL** (Kusto Query Language) by
**Kaushik Saha**: a KQL course you can run with an empty workspace, a library of 27 Sentinel and Defender XDR tables
with sample logs, a correlated attack scenario, an example analytic rule, and a reusable threat-hunting skill.

> **Learn KQL interactively → [verikql.kaushiksaha.com/learn](https://verikql.kaushiksaha.com/learn)**
>
> The **KQL Mastery Path** on VeriKQL takes you from your first query to closing a case, in six levels. Every
> query on the site is checked with Microsoft's own KQL parser against the real table schemas. This repository holds
> the source material behind the site's reference course and table library.

## What's here

| | What it is | Start with |
|---|---|---|
| **KQL reference course** | Five stages from setup to threat hunting, plus a cheat sheet, schema gotchas and Microsoft links. Stage 00 seeds a dataset, so you can practise with no logs flowing | [`sentinel/kql/`](sentinel/kql/README.md) |
| **Sentinel table library** | 27 Log Analytics and Defender XDR tables: what each holds, its full schema, gotchas, sample logs and MITRE ATT&CK-mapped hunts | [`sentinel/tables/`](sentinel/tables/README.md) |
| **Attack scenario: Operation Quiet Ledger** | One correlated incident across the tables, for triage practice and for testing analytic rules before you ship them | [`sentinel/tables/scenarios/operation-quiet-ledger/`](sentinel/tables/scenarios/operation-quiet-ledger/README.md) |
| **Example analytic rule** | Storage key theft followed by blob exfiltration, as KQL and as a deployable rule (YAML) | [`sentinel/analytic-rules/`](sentinel/analytic-rules/README.md) |
| **Labs and sample data** | Azure Data Explorer setup on a free cluster, with small teaching CSVs | [`sentinel/labs/`](sentinel/labs/README.md), [`sentinel/sampledata/`](sentinel/sampledata/README.md) |
| **Azure Sentinel Hunter skill** | A reusable skill for AI assistants: KQL authoring, detection engineering and threat hunting, with references, scripts and rule templates | [`.claude/skills/azure-sentinel-hunter/`](.claude/skills/azure-sentinel-hunter/SKILL.md) |

All sample data is synthetic (Contoso and Fabrikam users, placeholder subscription IDs). Nothing comes from a real
tenant.

## Check your own KQL

[**VeriKQL**](https://verikql.kaushiksaha.com) checks KQL for Microsoft Sentinel and Defender XDR with Microsoft's
own parser against a pinned table-schema bundle, and returns a proof record. It never runs your query and never sees
your logs. Use it on the site, or connect it to Claude or ChatGPT as an MCP server.

## Writing new material

New pages follow the [style guide](docs/docs_style_guide.md) and start from the
[document template](docs/templates/enterprise_doc_template.md). Every query is a fenced `kql` block.

## Licence

- **Written material** (the course, the table library, the scenario, the labs and the other Markdown documents) is
  licensed under [Creative Commons Attribution 4.0 International](LICENSE) (CC BY 4.0). You may share and adapt it,
  including commercially, if you credit **Kaushik Saha** and link to this repository.
- **Code** (KQL queries in `.kql` files, rule definitions, scripts and sample data) is licensed under the
  [MIT License](LICENSE-CODE).

Microsoft, Microsoft Sentinel, Microsoft Defender and Azure are trademarks of the Microsoft group of companies. This
repository is independent: it is not affiliated with, sponsored or endorsed by Microsoft.
