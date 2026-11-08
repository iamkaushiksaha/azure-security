# Documentation style guide

How pages in this repository are written. New pages start from the [page template](templates/page-template.md).

## Structure

- One H1 per page, plain text (no emoji). Don't skip heading levels.
- Open with one or two sentences on what the page is for and who it helps, then the content.
- An emoji may start a `##` heading as a signpost (🎯 purpose, 🧠 concept, 🧪 example, ✅ good practice,
  🚫 pitfall, 🚀 next step). Not in body text, tables or code.
- Link to other pages with relative links, and to Microsoft Learn for product facts.

## KQL

- Fence every query as ` ```kusto ` (GitHub highlights it as KQL; ` ```kql ` renders the same).
- One logical query per block, runnable as written: against a real table, the course's `DemoIdentityLogs`, or
  a `datatable()` in the block. Say which table it needs if it isn't obvious.
- Every query in this repository is checked with Microsoft's KQL parser against the Sentinel and Defender XDR
  table schemas before it's published ([VeriKQL](https://verikql.kaushiksaha.com)).
- Comment the why, not the what: thresholds, false-positive traps, and value types that surprise people
  (for example, `SigninLogs.ResultType` is a string).

## Detections and ATT&CK

- Map each hunt or rule to the most specific ATT&CK technique that's actually true, linked to
  attack.mitre.org, using the current ATT&CK release (v20 at the last check).
- State the hypothesis, the data it needs, the known false positives and how to tune it.

## Data

- Sample data is synthetic: Contoso and Fabrikam users, placeholder subscription IDs. Never paste logs from a
  real tenant.
- If an example uses real public IP ranges for realism, say so.

## Writing

- Plain, specific language. No marketing words ("enterprise-grade", "world-class"), no badges that can go stale.
- Product names as Microsoft writes them: Microsoft Sentinel, Microsoft Defender XDR, Microsoft Entra ID,
  Azure Data Explorer.
