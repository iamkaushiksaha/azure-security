# Detection engineering — building Sentinel analytic rules & use cases

How to turn a hypothesis into a **production analytic rule** that fires on real threats, maps to
ATT&CK, populates incident entities, and doesn't drown the SOC in false positives.

## The detection lifecycle

```
Hypothesis → KQL (schema-verified) → Test on sample data → Entity mapping + MITRE
   → False-positive tuning → Rule config (schedule/threshold/grouping) → Document → Deploy → Measure → Tune
```

Never skip *test* and *tune*. A rule shipped untested is a future incident-fatigue problem.

## Choose the rule type

| Type | Use when | Latency | Notes |
|---|---|---|---|
| **Scheduled** | Most detections; aggregation/join over a lookback | minutes | The workhorse. `queryFrequency`/`queryPeriod`. |
| **NRT (near-real-time)** | High-severity, single-table, need speed | ~1 min | One-table only, no unions of many tables, limited operators. |
| **Microsoft security** | Surface Defender/MDC alerts as incidents | — | Config, not KQL. |
| **Fusion** | ML multi-stage attack correlation | — | Managed by Microsoft; can't author the logic. |
| **Anomaly** | Behavioral/UEBA baselines | — | Tunable templates. |
| **Hunting query** | Not auto-alerting; analyst-run / scheduled hunts | — | Promote to scheduled rule when high-fidelity. |

## Write the detection query

Apply every [KQL best practice](kql-best-practices.md). Detection-specific additions:

- **Bound to the rule's window.** The query's `ago()` should match `queryPeriod`; don't scan 30d in
  a rule that runs every 5 min.
- **Emit entity columns.** The query must `project` the columns you'll map to entities (account,
  host, IP, URL, file hash) — un-mapped incidents are hard to triage and can't correlate.
- **Threshold in a `let`,** commented with its rationale, so tuning is one edit.
- **Make it idempotent across runs.** Use `queryFrequency == queryPeriod` unless you intend overlap;
  overlap re-alerts on the same rows.

## Entity mapping (do not skip)

Map query columns to Sentinel **entities** so incidents are investigable and **correlate/dedupe**:

| Entity | Common identifier(s) |
|---|---|
| Account | `Name` + `UPNSuffix`, or `AadUserId`, or NT `Sid` |
| Host | `HostName` / `FullName` / `AzureID` |
| IP | `Address` |
| URL / FileHash / Process / CloudApplication / MailMessage | per-entity fields |

Rules of thumb: map **2–3 strong entities** (e.g. Account + IP + Host); these drive incident
grouping and the investigation graph. In the rule YAML, `entityMappings` references the projected
column names.

## Map to MITRE ATT&CK

Every rule gets `tactics` and `techniques` (and sub-techniques where precise). This powers the
**MITRE coverage view** and threat-informed gap analysis. Pick the technique the *behavior* shows,
not the tool. Keep it honest — one accurate technique beats five aspirational ones. Maintain a
coverage layer (see the [scenario Navigator layer](../../../../sentinel/tables/scenarios/operation-quiet-ledger/mitre-navigator-layer.json)).

## False-positive tuning — the part that makes it deployable

Run the draft against the [sample data](../../../../sentinel/tables/README.md) **and** a realistic
baseline. The library's benign noise (legitimate admins `dvora`/`itadmin`, clean users `meganb`,
OAuth `GetBlob`) is exactly what trips over-broad rules. Tactics:

- **Allow-list known-good** via a **watchlist** (service accounts, scanners, VPN egress, admin
  jump hosts) — join `kind=leftanti` against it. Watchlists > hard-coded lists (tunable without
  editing the rule).
- **Baseline-relative** instead of absolute: "new" ASN/country/process vs the entity's own 14–30d
  history (`leftanti`/`set_has_element`), not a fixed threshold.
- **Require corroboration:** combine two weak signals (risky sign-in **and** a sensitive operation)
  so neither alone fires.
- **Severity by confidence.** Reserve High for high-fidelity; route hypotheses to hunting, not
  alerting.

## Rule configuration that matters

- **`queryFrequency` / `queryPeriod`:** how often it runs / how far back each run looks. Match them
  unless intentionally overlapping.
- **Threshold (`triggerOperator`/`triggerThreshold`):** usually `gt 0`; raise for noisy logic.
- **Event grouping:** `AlertPerResult` (one alert per row — good when each row is an actionable
  entity) vs `SingleAlert` (one alert per run — good for "N events of X").
- **Incident grouping:** group alerts into one incident by matching entities within a window — stops
  one campaign from creating 50 incidents.
- **Suppression:** stop re-firing on the same condition for N hours.
- **Lookback vs ingestion delay:** allow for ingestion latency (`queryPeriod` slightly > frequency,
  or use `ingestion_time()`), or the rule misses late-arriving rows.

A ready-to-edit rule is in [`../templates/scheduled-analytic-rule.yaml`](../templates/scheduled-analytic-rule.yaml);
scaffold one from a query with `scripts/scaffold_analytic_rule.py`.

## Document & operationalize

For each detection record: name, description, **hypothesis**, ATT&CK mapping, data sources/tables,
**required connectors**, severity, **known false positives & tuning**, validation evidence (it fired
on the sample), and triage/response steps. Store detections **as code** (YAML in version control,
deploy via the [Sentinel repositories / CI-CD connection](https://learn.microsoft.com/en-us/azure/sentinel/ci-cd))
so changes are reviewed and auditable — the same discipline as application code.

## Measure & maintain
- Track **true-positive / false-positive rate** per rule; retire or tune chronic noise.
- Watch for **schema drift** (a connector update renames/retires a column) — the query silently
  breaks. Re-validate against MS Learn periodically.
- Re-test after edits using the sample data so a "small tweak" doesn't widen the net.

References: [Create scheduled analytic rules](https://learn.microsoft.com/en-us/azure/sentinel/detect-threats-custom) ·
[Map data fields to entities](https://learn.microsoft.com/en-us/azure/sentinel/map-data-fields-to-entities) ·
[NRT rules](https://learn.microsoft.com/en-us/azure/sentinel/near-real-time-rules) ·
[Surface anomalies / tuning](https://learn.microsoft.com/en-us/azure/sentinel/detection-tuning) ·
[MITRE coverage](https://learn.microsoft.com/en-us/azure/sentinel/mitre-coverage)
