#!/usr/bin/env python3
"""
csv_to_kql.py — turn a Sentinel Table Library sample CSV into runnable KQL.

Why: lets you test a query/detection with NO populated workspace and NO write
permissions. Emits either a `let <Table> = datatable(...)[...]` block you paste
above your query (works in Log Analytics, Sentinel AND Azure Data Explorer), or
ADX control commands to ingest into a free cluster (https://aka.ms/kustofree).

Column TYPES are taken from the sibling README.md schema table when present (the
library's MS-Learn-validated types), so columns like SigninLogs.ResultType stay
STRING even though the values look numeric. Falls back to value inference for any
column the schema table doesn't list.

Usage:
    python3 csv_to_kql.py <path/to/Table_sample.csv> [--mode datatable|adx] [--rebase]

    --mode datatable   (default) emit a `let <Table> = datatable(...)` block
    --mode adx         emit `.create table` + `.ingest inline` control commands
    --rebase           rewrite TimeGenerated to now()-relative so `ago()` filters
                       in the table's hunts match today (datatable mode only)

Examples:
    python3 csv_to_kql.py sentinel/tables/SigninLogs/SigninLogs_sample.csv
    python3 csv_to_kql.py sentinel/tables/SigninLogs/SigninLogs_sample.csv --mode adx
    python3 csv_to_kql.py sentinel/tables/DnsEvents/DnsEvents_sample.csv --rebase
"""
import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone

KQL_TYPES = {"string", "int", "long", "real", "double", "datetime", "bool", "dynamic", "guid", "timespan"}
_NORMALISE = {"double": "real", "guid": "string"}  # map to datatable-friendly types


def parse_schema_types(readme_path):
    """Extract {column: kqltype} from the markdown schema table in a table README."""
    types = {}
    if not os.path.exists(readme_path):
        return types
    with open(readme_path, encoding="utf-8") as f:
        for line in f:
            # rows look like:  | ColumnName | type | description |
            m = re.match(r"\s*\|\s*`?([A-Za-z0-9_]+)`?\s*\|\s*`?([A-Za-z0-9_]+)`?\s*\|", line)
            if not m:
                continue
            col, typ = m.group(1), m.group(2).lower()
            if typ in KQL_TYPES and col.lower() not in ("column", "name"):
                types[col] = _NORMALISE.get(typ, typ)
    return types


_INT_RE = re.compile(r"^-?\d+$")
_REAL_RE = re.compile(r"^-?\d+\.\d+(e-?\d+)?$", re.I)
_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")


def infer_type(values):
    """Conservative value-based type inference for columns missing from the schema."""
    vals = [v for v in values if v != ""]
    if not vals:
        return "string"
    def all_match(pred):
        return all(pred(v) for v in vals)
    if all_match(lambda v: v.lower() in ("true", "false")):
        return "bool"
    if all_match(lambda v: _INT_RE.match(v)):
        return "long"  # long is safe for ids/epochs; values like "0" are kept numeric only if schema agrees
    if all_match(lambda v: _REAL_RE.match(v) or _INT_RE.match(v)):
        return "real"
    if all_match(lambda v: bool(_ISO_RE.match(v))):
        return "datetime"
    if all_match(lambda v: v[:1] in "{[" and v[-1:] in "}]" and _is_json(v)):
        return "dynamic"
    return "string"


def _is_json(v):
    try:
        json.loads(v)
        return True
    except Exception:
        return False


def fmt_datatable_value(v, typ):
    if v == "":
        return {"string": '""'}.get(typ, f"{typ}(null)")
    if typ == "string":
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if typ in ("int", "long", "real"):
        return v
    if typ == "bool":
        return v.lower()
    if typ == "datetime":
        return f"datetime({v})"
    if typ == "timespan":
        return f"timespan({v})"
    if typ == "dynamic":
        return f"dynamic({v})"
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def table_name_from_path(path):
    base = os.path.basename(path)
    base = re.sub(r"\.csv$", "", base, flags=re.I)
    base = re.sub(r"_sample.*$", "", base, flags=re.I)
    return base


def load(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = [r for r in reader if r]
    header, data = rows[0], rows[1:]
    return header, data


def compute_offsets(header, data):
    """Return list of timespan strings (now - TimeGenerated) for --rebase, anchored so newest row ~= now."""
    if "TimeGenerated" not in header:
        return None
    ti = header.index("TimeGenerated")
    parsed = []
    for r in data:
        v = r[ti]
        try:
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None
        parsed.append(dt)
    newest = max(parsed)
    offs = []
    for dt in parsed:
        secs = int((newest - dt).total_seconds())
        d, rem = divmod(secs, 86400)
        h, rem = divmod(rem, 3600)
        m, s = divmod(rem, 60)
        offs.append(f"{d}.{h:02d}:{m:02d}:{s:02d}")
    return offs


def emit_datatable(table, header, data, types, rebase):
    offsets = compute_offsets(header, data) if rebase else None
    cols = list(header)
    coltypes = [types.get(c) or infer_type([r[i] for r in data]) for i, c in enumerate(cols)]

    out = []
    out.append(f"// {table} — {len(data)} rows. Paste above your query and run (no ingestion needed).")
    if offsets:
        out.append("// --rebase: TimeGenerated is now()-relative so ago() filters match today.")
    out.append(f"let {table} = (")

    if offsets:
        # replace TimeGenerated literal column with an offset column, rebuild time via extend
        ti = cols.index("TimeGenerated")
        decl = [f"    {c}:{t}" for c, t in zip(cols, coltypes) if c != "TimeGenerated"]
        decl.insert(ti, "    _Off:timespan")
        out.append("datatable(")
        out.append(",\n".join(decl))
        out.append(")[")
        for r, off in zip(data, offsets):
            cells = []
            for i, (c, t) in enumerate(zip(cols, coltypes)):
                if c == "TimeGenerated":
                    cells.append(f"timespan({off})")
                else:
                    cells.append(fmt_datatable_value(r[i], t))
            out.append("    " + ", ".join(cells) + ",")
        out[-1] = out[-1].rstrip(",")
        out.append("]")
        out.append("| extend TimeGenerated = now() - _Off")
        out.append("| project-away _Off")
    else:
        decl = [f"    {c}:{t}" for c, t in zip(cols, coltypes)]
        out.append("datatable(")
        out.append(",\n".join(decl))
        out.append(")[")
        for r in data:
            cells = [fmt_datatable_value(r[i], t) for i, t in enumerate(coltypes)]
            out.append("    " + ", ".join(cells) + ",")
        out[-1] = out[-1].rstrip(",")
        out.append("]")
    out.append(");")
    out.append(f"{table}")
    out.append("| take 100")
    return "\n".join(out)


def emit_adx(table, header, data, types, raw_path):
    cols = list(header)
    coltypes = [types.get(c) or infer_type([r[i] for r in data]) for i, c in enumerate(cols)]
    out = []
    out.append(f"// {table} — ADX free-cluster ingestion (https://dataexplorer.azure.com).")
    out.append(f".drop table {table} ifexists")
    out.append("")
    decl = ", ".join(f"{c}:{t}" for c, t in zip(cols, coltypes))
    out.append(f".create table {table} ({decl})")
    out.append("")
    out.append(f".ingest inline into table {table} with (format='csv', ignoreFirstRecord=true) <|")
    with open(raw_path, encoding="utf-8-sig") as f:
        body = f.read().splitlines()
    for line in body:
        out.append(line)
    out.append("")
    out.append(f"{table} | take 100")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Convert a Sentinel sample CSV to runnable KQL.")
    ap.add_argument("csv_path")
    ap.add_argument("--mode", choices=["datatable", "adx"], default="datatable")
    ap.add_argument("--rebase", action="store_true", help="now()-relative TimeGenerated (datatable mode)")
    args = ap.parse_args()

    if not os.path.exists(args.csv_path):
        sys.exit(f"error: no such file: {args.csv_path}")

    table = table_name_from_path(args.csv_path)
    header, data = load(args.csv_path)
    types = parse_schema_types(os.path.join(os.path.dirname(args.csv_path), "README.md"))

    if args.mode == "adx":
        if args.rebase:
            sys.stderr.write("note: --rebase ignored in adx mode (inline ingest keeps literal times)\n")
        print(emit_adx(table, header, data, types, args.csv_path))
    else:
        print(emit_datatable(table, header, data, types, args.rebase))


if __name__ == "__main__":
    main()
