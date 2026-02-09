# Documentation Style Guide

This guide defines **mandatory standards** for all Markdown documentation in this repository.

---

## 1. Heading Rules

- One `#` (H1) per document
- Do not skip heading levels
- Emojis allowed only in `##` section headers

---

## 2. Emoji Usage (Approved Set Only)

| Emoji | Meaning |
|----|--------|
| 🎯 | Purpose |
| 🧠 | Concept |
| 🧩 | Components |
| ⏱️ | Time / Performance |
| 🚫 | Mistakes |
| ✅ | Best Practice |
| 🧪 | Examples |
| 🚀 | Next steps |

❌ No emojis in:
- Paragraph text
- Tables
- Code blocks

---

## 3. KQL Rules (Non-Negotiable)

✔ All KQL must be fenced  
✔ Use ```kql language tag  
✔ One logical query per block  
✔ No inline multi-line KQL  

Example:

```kql
SigninLogs
| take 10
```

---

## 4. Section Order

Recommended order:

1. Why this document exists  
2. Data / Context  
3. Core concept  
4. Key components  
5. Time / performance  
6. Mistakes  
7. Best practices  
8. Examples  
9. What’s next  

---

## 5. General Principles

- Scannable before detailed
- Explain *why* before *how*
- Prefer tables for schemas
- Keep examples realistic

---

> Documents not following this guide may be rejected during review.
