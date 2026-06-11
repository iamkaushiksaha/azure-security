# Schema Gotchas — the errors that silently break queries

Column-name and data-type mistakes don't always error — they return wrong or empty results. These are the traps this lab calls out, each verified against the Microsoft table reference.

## 1. `ResultType` is a STRING in real `SigninLogs` (but an INT in the demo set)

- **Real `SigninLogs`:** `ResultType` is **`string`** (e.g. `"0"`, `"50126"`). `"0"` = success. → use `where ResultType != "0"`.
- **Seeded `DemoIdentityLogs`:** declared as **`int`** for teaching simplicity. → use `where ResultType != 0`.

Mixing them isn't always fatal (KQL may coerce), but `== 0` vs `== "0"` confusion is the #1 beginner bug. Match the type to the table.
Source: [SigninLogs table reference](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/signinlogs)

## 2. `AuditLogs.InitiatedBy` is a dynamic (nested) column — not a flat UPN

Actor identity lives **inside** the `dynamic` `InitiatedBy` object. `tostring(InitiatedBy)` serialises the whole JSON blob (messy, won't join cleanly). Drill in instead:

```kusto
AuditLogs
| extend Actor = tostring(InitiatedBy.user.userPrincipalName)
```

`TargetResources` is a dynamic **array** — index it (`TargetResources[0].displayName`) or `mv-expand` it.
Source: [AuditLogs table reference](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/auditlogs)

## 3. Column-name casing differs across tables

The same concept is spelled differently table to table — never assume. Always confirm against the table reference:

| Concept | `SigninLogs` | `CommonSecurityLog` | `DeviceNetworkEvents` |
|---|---|---|---|
| Source IP | `IPAddress` | `SourceIP` | `LocalIP` / `RemoteIP` |

When in doubt: `<table> | getschema` or check `learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/<tablename>`.

## 4. ASIM unifying parsers need the leading underscore — and lowercase call params

- Parser name: **`_Im_Dns`**, **`_Im_Authentication`** (with leading `_`), invoked like a function.
- **Filtering parameters in the call are lowercase**: `starttime=`, `responsecodename=`, `eventresult=`.
- **Output fields are PascalCase**: `ResponseCodeName`, `SrcIpAddr`, `TargetUserId`.

```kusto
_Im_Authentication(starttime=ago(1h), eventresult='Failure')
| summarize count() by TargetUserId
```
Source: [Use ASIM parsers](https://learn.microsoft.com/en-us/azure/sentinel/normalization-about-parsers)

## 5. Basic-plan tables have query restrictions

Some tables (e.g. `DeviceProcessEvents`, `DeviceNetworkEvents`, `SigninLogs` are flagged *Basic log: Yes* in their reference) may sit on the **Basic** log plan, which limits operators and retention behaviour. Check the table plan before writing heavy aggregation/`join` over long ranges.
Source: [Table plans (Analytics vs Basic)](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/logs-table-plans?tabs=portal-1)

## 6. Validation protocol (do this before finalising any query)

1. Confirm the **table** exists: `learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/<tablename>`.
2. Confirm **every column name and type** against that page — don't trust memory.
3. Note **dynamic/nested** columns and `extend`/`parse_json` them.
4. Check the **table plan** for restrictions.
5. If a column can't be verified, flag it in a `// ⚠️ WARNING:` comment rather than guessing.
