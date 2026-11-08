# <Title>

<One or two sentences: what this page is for and who it helps.>

> **Audience:** <who this is for>
> **Needs:** <tables or data, e.g. SigninLogs, or the course's DemoIdentityLogs>

## 🎯 Why this matters

- The problem
- Why it matters
- When to use this page

## 🧠 The idea

Explain the concept before the syntax.

## 🧪 Example

```kusto
// What this query finds, and why
SigninLogs
| where TimeGenerated > ago(1d)
| where ResultType == "50126"            // invalid username or password; ResultType is a string
| summarize Failures = count() by UserPrincipalName
| top 10 by Failures
```

## 🚫 Pitfalls

- <A mistake people make, and how to avoid it>

## ✅ Good practice

- <What to do instead>

## 🚀 Next

- <Related pages>

<!-- Checklist before publishing (see ../style-guide.md):
     - every query is runnable and passes VeriKQL
     - ATT&CK IDs are current and the most specific true technique
     - sample data is synthetic -->
