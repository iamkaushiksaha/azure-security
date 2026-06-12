# Threat-hunting methodology

Hunting is **proactive, hypothesis-driven** search for activity that evaded existing detections —
not random querying. This is the loop, the discipline, and the KQL patterns that make it repeatable.

## The hunt loop (PEAK / TaHiTI-aligned)

```
1. Hypothesis   — a specific, falsifiable claim ("an actor is using DNS TXT for C2 on finance hosts")
2. Scope        — tables, time window, entities, expected normal
3. Hunt (broad) — cast wide, eyeball the top, learn the baseline
4. Pivot        — chase strong indicators across tables (same IP/user/host/hash)
5. Conclude     — confirmed / refuted / inconclusive (+ what would resolve it)
6. Output       — document; promote high-fidelity findings to a detection; note coverage gaps
```

A good hypothesis is **specific and testable** and ideally **threat-informed** (a MITRE technique,
a TI report, a crown-jewel risk). "Look for bad things" is not a hypothesis.

## Where hypotheses come from
- **MITRE ATT&CK** — pick a technique relevant to your estate, ask "would we see it?" Map your
  coverage with the [Navigator layer](../../../../sentinel/tables/scenarios/operation-quiet-ledger/mitre-navigator-layer.json).
- **Threat intel** — a new TTP/IOC report → "is this present in our data?"
- **Crown jewels** — start from the asset (finance storage, DCs, KeyVault) and work outward.
- **Anomaly** — a spike/gap/new-value worth explaining.
- **Incident retro** — "what *else* would this actor have done that we didn't alert on?"

## Run broad, then tighten

Start permissive to learn normal, then add precision. Don't over-filter before you understand the
baseline — you'll filter away the thing you're hunting.

```kusto
// Broad: what interpreters made public connections today, ranked
DeviceNetworkEvents
| where TimeGenerated > ago(1d) and RemoteIPType == "Public"
| where InitiatingProcessFileName in~ ("powershell.exe","pwsh.exe","cmd.exe","wscript.exe","cscript.exe","mshta.exe","rundll32.exe","regsvr32.exe")
| summarize Conns = count(), Hosts = make_set(RemoteUrl, 50) by DeviceName, InitiatingProcessFileName
| sort by Conns desc
```

## Pivot on the strongest indicator

When something looks off, pivot the **highest-value indicator** across tables. The
[table library](../../../../sentinel/tables/README.md) "Correlates with" sections and the
[Operation Quiet Ledger join queries](../../../../sentinel/tables/scenarios/operation-quiet-ledger/README.md)
are a worked pivot map. Think **Pyramid of Pain** — pivoting on TTPs/behaviors (process lineage,
auth pattern) costs the adversary more than chasing hashes/IPs they rotate freely.

```kusto
// Pivot: everything one IP touched, across identity + cloud + endpoint
let ioc = "185.220.101.2";
union
  (SigninLogs      | where IPAddress == ioc | extend T="Signin",  Who=UserPrincipalName),
  (AzureActivity   | where CallerIpAddress has ioc | extend T="ARM", Who=Caller),
  (DeviceLogonEvents | where RemoteIP == ioc | extend T="Logon",  Who=AccountName),
  (StorageBlobLogs | where CallerIpAddress has ioc | extend T="Blob", Who=RequesterUpn)
| project TimeGenerated, T, Who, IOC=ioc
| sort by TimeGenerated asc
```

## Baselining & anomaly techniques

- **First-seen / rare-value:** compare a recent window to a historical one with `leftanti` or
  `set_has_element` (new process, new ASN, new admin) — see [kql-best-practices.md](kql-best-practices.md).
- **Statistical series:** `make-series` over time then `series_decompose_anomalies()` to flag
  spikes/dips with trend+seasonality removed.
- **Frequency/stack counting:** `summarize count() by X | where count_ < N` to surface the rare —
  "least frequency of occurrence" is a classic hunting lens.
- **Regularity/beaconing:** delta-between-events with low `stdev` = automation (DNS/network C2).

## Scope discipline
- **Time-bound** to the hypothesis window; widen only when a lead justifies it.
- **Watch performance** — hunts run interactively; filter early, sample with `take` while iterating,
  then remove the sample for the real run.
- **Separate signal from noise deliberately** — know what *normal* looks like for the scoped
  entities before calling something anomalous.

## Conclude & output

Every hunt ends with a verdict and an artifact, even a negative one (negative results document
coverage and save the next hunter time):

- **Confirmed →** raise an incident; capture the query and IOCs; **promote to a detection** if it can
  run continuously (see [detection-engineering.md](detection-engineering.md)).
- **Refuted →** record the hypothesis, the query, and why it's clear.
- **Inconclusive →** note the missing data/visibility — that's a **logging gap** to close (a finding
  in itself; e.g. the `Usage`/`Heartbeat` "source went silent" tell).
- Always: update your **ATT&CK coverage** and file the hunt with [`../templates/hunt-report.md`](../templates/hunt-report.md).

## Bundled practice data

The [Operation Quiet Ledger scenario](../../../../sentinel/tables/scenarios/operation-quiet-ledger/README.md)
is a full intrusion across 18 tables with benign noise — ideal for rehearsing the loop end to end:
form a hypothesis from one table, pivot to full blast radius, and write it up.

References: [Hunt for threats with Sentinel](https://learn.microsoft.com/en-us/azure/sentinel/hunting) ·
[Advanced hunting (Defender XDR)](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-overview) ·
[MITRE ATT&CK](https://attack.mitre.org/)
