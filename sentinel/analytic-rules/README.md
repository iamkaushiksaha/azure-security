# Microsoft Sentinel — Analytic Rules

Production-style **scheduled analytic rules** as code, organized by primary [MITRE ATT&CK](https://attack.mitre.org/) tactic. Each rule is authored with the [Azure Sentinel Hunter skill](../../.claude/skills/azure-sentinel-hunter/SKILL.md) and **tested against the [table library](../tables/README.md) sample data** before it lands here.

## Layout

```
analytic-rules/
├── credential-access/
│   ├── storage-key-theft-blob-exfil.kql    # the detection query (schema-verified)
│   └── storage-key-theft-blob-exfil.yaml   # the deployable rule (entities, MITRE, tuning)
└── privilege-escalation/
```

Each detection ships as a pair: a **`.kql`** (the query, readable and reviewable on its own) and a **`.yaml`** (the full Sentinel rule — entity mappings, MITRE, grouping, suppression). The YAML follows the Sentinel repository / API format and deploys via the [Sentinel repositories CI/CD connection](https://learn.microsoft.com/en-us/azure/sentinel/ci-cd).

## How a rule gets here (the bar)

Every rule meets the skill's **definition of done**:
- columns verified against the table library / Microsoft Learn (types and identity columns correct);
- time-bounded and filtered early;
- **tested on sample data** — catches the true positives, quiet on the benign noise (evidence noted in the YAML);
- mapped to real ATT&CK techniques;
- entity mappings + a written false-positive / tuning note.

## Rules

| Rule | Tactic(s) | Techniques | What it catches |
|---|---|---|---|
| [storage-key-theft-blob-exfil](credential-access/storage-key-theft-blob-exfil.yaml) | Credential Access · Collection · Exfiltration | T1552 · T1530 · T1567 | `listKeys` then bulk **AccountKey** blob reads from the same IP — key theft → exfil, bridged across control/data plane |

> Test any rule yourself: ingest the relevant table samples (see the [library README](../tables/README.md#-how-to-use-this-library)) or generate a runnable `datatable` with the skill's `csv_to_kql.py`, then run the `.kql`. A correct rule returns the attacker rows (`185.220.101.2`) and ignores the benign noise.
