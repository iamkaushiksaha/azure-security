# Microsoft Sentinel — Analytic Rules

Production-style **scheduled analytic rules** as code, organized by primary [MITRE ATT&CK](https://attack.mitre.org/) tactic. Each rule is authored with the [Azure Sentinel Hunter skill](../../.claude/skills/azure-sentinel-hunter/SKILL.md) and **tested against the [table library](../tables/README.md) sample data** before it lands here.

## Layout

```
analytic-rules/
└── credential-access/
    ├── storage-key-theft-blob-exfil.kql    # the detection query (schema-verified)
    └── storage-key-theft-blob-exfil.yaml   # the full rule (entities, MITRE, tuning)
```

Each detection ships as a pair: a **`.kql`** (the query, readable and reviewable on its own) and a **`.yaml`** (the full Sentinel rule — entity mappings, MITRE, grouping, suppression). The YAML is in the [Azure-Sentinel GitHub community detection format](https://github.com/Azure/Azure-Sentinel/tree/master/Detections) (durations written as `1h` / `3h`, not ISO `PT1H`). [Sentinel Repositories](https://learn.microsoft.com/en-us/azure/sentinel/ci-cd) deploys ARM templates (and Bicep), not this YAML: to deploy with Repositories, convert the rule to an ARM template first, or paste the `.kql` into the analytics rule wizard and set the schedule, entities and MITRE from the YAML.

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
| [storage-key-theft-blob-exfil](credential-access/storage-key-theft-blob-exfil.yaml) | Credential Access · Collection · Exfiltration | T1552 · T1530 · T1567 | `listKeys` / `listAccountSas` then bulk **AccountKey / SAS** blob reads of the same storage account from the same IP — key theft → exfil, bridged across control/data plane |

> Test any rule yourself: ingest the relevant table samples (see the [library README](../tables/README.md#-how-to-use-this-library)) or generate a runnable `datatable` with the skill's `csv_to_kql.py`, then run the `.kql`. The samples carry fixed dates, and the rules filter with `ago(...)`, so **rebase the timestamps first** or the query finds nothing:
>
> ```
> python3 .claude/skills/azure-sentinel-hunter/scripts/csv_to_kql.py sentinel/tables/AzureActivity/AzureActivity_sample.csv --rebase
> python3 .claude/skills/azure-sentinel-hunter/scripts/csv_to_kql.py sentinel/tables/StorageBlobLogs/StorageBlobLogs_sample.csv --rebase
> ```
>
> Paste each `let <Table> = ...;` block above the `.kql` (drop the trailing `<Table> | take 100` lines). `--rebase` anchors each table's newest row to now on its own, so gaps *between* tables can shift by a few minutes; the storage example still correlates. A correct rule returns the attacker rows (`185.220.101.2`) and ignores the benign noise.
