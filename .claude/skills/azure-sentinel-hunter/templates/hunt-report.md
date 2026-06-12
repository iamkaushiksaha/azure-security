# Threat Hunt Report — <short title>

| | |
|---|---|
| **Hunt ID** | HUNT-YYYY-NNN |
| **Date** | YYYY-MM-DD |
| **Hunter(s)** | <name> |
| **Status** | 🟡 In progress · ✅ Confirmed · ⚪ Refuted · 🔵 Inconclusive |
| **Duration** | <hours> |

## Hypothesis
A specific, falsifiable statement of what you expect to find and why.
> Example: "An external actor compromised a finance account and used it to escalate Azure RBAC
> and exfiltrate from blob storage within a 4-hour window."

## Threat / driver
What prompted this hunt — MITRE technique, TI report, crown-jewel risk, anomaly, or incident retro.
- **ATT&CK:** Txxxx(.xxx) — <tactic / technique name>
- **Source:** <TI ref / risk / anomaly>

## Scope
- **Tables:** <e.g. SigninLogs, AzureActivity, StorageBlobLogs>
- **Time window:** <start → end>
- **Entities / assets:** <users, hosts, subscriptions, resources>
- **Assumed normal:** <what benign looks like for this scope>

## Method & queries
The queries run, in order, with what each was looking for. Keep them runnable.

```kusto
// <what this step tests>
<query>
```

## Findings
What you actually observed — evidence, counts, screenshots/links. Distinguish fact from inference.

| Time | Entity | Observation | Evidence (table/row) |
|---|---|---|---|
| | | | |

## Pivots followed
The indicators you chased and where they led (Pyramid of Pain — prefer TTP/behavior pivots).

## Verdict
- [ ] **Confirmed** — malicious/risky activity found → raise incident `#____`, capture IOCs below.
- [ ] **Refuted** — hypothesis not supported; activity explained by <…>.
- [ ] **Inconclusive** — could not resolve; blocked by <missing data / visibility gap>.

## IOCs / observables
| Type | Value | Notes |
|---|---|---|
| IP / domain / hash / account | | |

## Outcomes & follow-ups
- [ ] **Promote to detection?** If continuously runnable → analytic rule (link the rule / PR).
- [ ] **Coverage gap?** Missing log source / DCR filter / Basic-plan limit to fix.
- [ ] **ATT&CK coverage updated** (Navigator layer).
- [ ] **Response actions** handed to IR (isolate, reset, revoke, block).

## Lessons / notes
What the next hunter should know — false-positive sources, better pivots, query tuning.
