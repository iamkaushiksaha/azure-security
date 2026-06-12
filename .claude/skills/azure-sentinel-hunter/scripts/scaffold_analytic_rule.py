#!/usr/bin/env python3
"""
scaffold_analytic_rule.py — generate a Microsoft Sentinel scheduled analytic rule
(YAML) from a KQL query and metadata. Output matches the Sentinel repository /
API format (Microsoft.SecurityInsights alertRules), ready to commit and deploy.

Zero dependencies (hand-emitted YAML). Pipe to a file in your detections repo.

Usage:
    python3 scaffold_analytic_rule.py \
        --name "Sign-in success from new ASN after brute force" \
        --query-file detection.kql \
        --severity High \
        --tactics CredentialAccess,InitialAccess \
        --techniques T1110,T1078 \
        --frequency 1h --period 1h \
        --account-col UserPrincipalName --ip-col IPAddress \
        > rule.yaml

Notes:
  * Always pair with references/detection-engineering.md (entity mapping, tuning).
  * Replace the placeholder id with a real GUID before deploying.
  * Map at least 2-3 entities so incidents correlate and dedupe.
"""
import argparse
import sys

ENTITY_IDS = {  # cli flag -> (entityType, identifier)
    "account_col": ("Account", "FullName"),
    "ip_col": ("IP", "Address"),
    "host_col": ("Host", "HostName"),
    "url_col": ("URL", "Url"),
    "filehash_col": ("FileHash", "Value"),
}


def block_scalar(text, indent):
    pad = " " * indent
    return "\n".join(pad + line if line else pad.rstrip() for line in text.rstrip("\n").splitlines())


def main():
    ap = argparse.ArgumentParser(description="Scaffold a Sentinel scheduled analytic rule (YAML).")
    ap.add_argument("--name", required=True)
    ap.add_argument("--description", default="TODO: hypothesis, what it detects, and known false positives.")
    ap.add_argument("--query-file", help="file containing the detection KQL")
    ap.add_argument("--query", help="inline KQL (alternative to --query-file)")
    ap.add_argument("--severity", default="Medium", choices=["Informational", "Low", "Medium", "High"])
    ap.add_argument("--tactics", default="", help="comma-separated ATT&CK tactics (e.g. CredentialAccess)")
    ap.add_argument("--techniques", default="", help="comma-separated technique IDs (e.g. T1110,T1078)")
    ap.add_argument("--frequency", default="1h", help="queryFrequency (e.g. 5m, 1h)")
    ap.add_argument("--period", default="1h", help="queryPeriod / lookback (e.g. 1h, 1d)")
    ap.add_argument("--threshold", type=int, default=0, help="triggerThreshold (results > N)")
    ap.add_argument("--grouping", default="SingleAlert", choices=["SingleAlert", "AlertPerResult"])
    for flag in ENTITY_IDS:
        ap.add_argument(f"--{flag.replace('_', '-')}", dest=flag, help=f"column to map to {ENTITY_IDS[flag][0]} entity")
    args = ap.parse_args()

    if args.query_file:
        with open(args.query_file, encoding="utf-8") as f:
            query = f.read()
    elif args.query:
        query = args.query
    else:
        query = "// TODO: paste your schema-verified, time-bounded detection KQL here\nTableName\n| where TimeGenerated > ago(1h)\n"

    def fmt_dur(d):  # 5m/1h/1d -> ISO8601 duration
        n, unit = d[:-1], d[-1].lower()
        return {"m": f"PT{n}M", "h": f"PT{n}H", "d": f"P{n}D"}.get(unit, d)

    lines = []
    lines.append("id: 00000000-0000-0000-0000-000000000000   # TODO replace with a real GUID")
    lines.append(f"name: {args.name}")
    lines.append("kind: Scheduled")
    lines.append("description: |")
    lines.append(block_scalar(args.description, 2))
    lines.append(f"severity: {args.severity}")
    lines.append("requiredDataConnectors: []   # TODO list connectors the query depends on")
    lines.append(f"queryFrequency: {fmt_dur(args.frequency)}")
    lines.append(f"queryPeriod: {fmt_dur(args.period)}")
    lines.append("triggerOperator: gt")
    lines.append(f"triggerThreshold: {args.threshold}")
    tactics = [t.strip() for t in args.tactics.split(",") if t.strip()]
    lines.append("tactics:" + (" []" if not tactics else ""))
    for t in tactics:
        lines.append(f"  - {t}")
    techs = [t.strip() for t in args.techniques.split(",") if t.strip()]
    lines.append("relevantTechniques:" + (" []" if not techs else ""))
    for t in techs:
        lines.append(f"  - {t}")
    lines.append("query: |")
    lines.append(block_scalar(query, 2))

    mapped = [(ENTITY_IDS[f], getattr(args, f)) for f in ENTITY_IDS if getattr(args, f)]
    lines.append("entityMappings:" + (" []   # TODO map 2-3 entities" if not mapped else ""))
    for (etype, ident), col in mapped:
        lines.append(f"  - entityType: {etype}")
        lines.append("    fieldMappings:")
        lines.append(f"      - identifier: {ident}")
        lines.append(f"        columnName: {col}")

    lines.append("eventGroupingSettings:")
    lines.append(f"  aggregationKind: {args.grouping}")
    lines.append("incidentConfiguration:")
    lines.append("  createIncident: true")
    lines.append("  groupingConfiguration:")
    lines.append("    enabled: true")
    lines.append("    reopenClosedIncident: false")
    lines.append("    lookbackDuration: PT5H")
    lines.append("    matchingMethod: AllEntities")
    lines.append("suppressionEnabled: false")
    lines.append("suppressionDuration: PT1H")
    lines.append("version: 1.0.0")

    sys.stdout.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
