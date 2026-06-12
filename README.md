# Azure Security
### Enterprise-Grade Microsoft Sentinel & Cloud Security Repository

> **Maintainer:** Kaushik Saha  
> **Focus Areas:** Microsoft Sentinel, KQL, Detection Engineering, Threat Hunting, Azure Security  
> **Audience:** SOC Analysts, Threat Hunters, Security Engineers, Cloud Security Architects

---

## 🎯 Repository Purpose

This repository provides **enterprise-ready, hands-on security content** focused on:

- Microsoft Sentinel (SIEM / SOAR)
- Kusto Query Language (KQL)
- Threat hunting and detection engineering
- Azure security telemetry and log analytics

The goal is to move beyond copy‑paste queries and help practitioners **think like security analysts and detection engineers**.

---

## 🧠 What You’ll Find Here

- 📘 **Conceptual guides** (KQL fundamentals, mental models, best practices)
- 🧪 **Hands-on labs** for Sentinel and Azure Data Explorer
- 🛡️ **Detection engineering examples**
- 🔍 **Threat hunting queries**
- 📊 **Sample datasets** for practice and learning

All documentation follows a **consistent enterprise documentation standard**.

### ⭐ Featured

- **[KQL Mastery Path](sentinel/kql/README.md)** — a 5-stage course from novice to threat hunter, runnable even with an empty workspace.
- **[Sentinel Table Library](sentinel/tables/README.md)** — 21 schema-validated tables, each with sample logs, gotchas, and MITRE-mapped hunts, woven into one correlated [attack scenario](sentinel/tables/scenarios/operation-quiet-ledger/README.md) for triage and analytic-rule testing.
- **[Azure Sentinel Hunter skill](.claude/skills/azure-sentinel-hunter/SKILL.md)** — a reusable KQL / detection-engineering / threat-hunting skill (methodology, references, scripts, rule templates).

---

## 📂 Repository Structure

```
azure-security/
├── docs/
│   ├── DOCS_STYLE_GUIDE.md
│   └── templates/
│       └── ENTERPRISE_DOC_TEMPLATE.md
├── sentinel/
│   ├── docs/
│   ├── kql/            # KQL Mastery Path — novice → threat hunter
│   ├── tables/         # Table library — 21 schemas + sample logs + correlated scenario
│   ├── sampledata/
│   └── labs/
├── .claude/
│   └── skills/
│       └── azure-sentinel-hunter/   # KQL / detection-engineering / threat-hunting skill
├── detections/
├── hunting/
└── README.md
```

---

## 🚀 Getting Started

### 1️⃣ Learn KQL Fundamentals
Start with the KQL basics and mental models before jumping into detections.

### 2️⃣ Run the Labs
Use provided sample data to practice queries in:
- Microsoft Sentinel
- Azure Data Explorer (ADX)

### 3️⃣ Build Detections
Apply concepts to:
- Scheduled analytics rules
- Hunting queries
- Incident investigations

---

## 🧪 Example Technologies Covered

- Microsoft Sentinel
- Azure Monitor Logs
- Azure Data Explorer (ADX)
- Microsoft Defender
- MITRE ATT&CK

---

## 🤝 Contributions

Contributions are welcome, provided they:

- Follow the documentation style guide
- Use the enterprise templates
- Include fenced KQL queries
- Maintain clarity and intent

Pull requests that do not follow standards may be requested for revision.

---

## 📐 Documentation Standards (Important)

All documentation in this repository follows defined standards:

- **Enterprise Markdown structure**
- **Mandatory KQL fencing**
- **Consistent section order**
- **Controlled emoji usage (semantic only)**

📘 Read the full standards here:  
👉 `docs/DOCS_STYLE_GUIDE.md`

To create new documentation, always start from:  
👉 `docs/templates/ENTERPRISE_DOC_TEMPLATE.md`

---

## 📌 Disclaimer

This repository is for **educational and research purposes**.  
Content is not affiliated with or endorsed by Microsoft.

---

## ⭐ Final Note

If this repository helps you learn, build, or teach cloud security —  
consider starring ⭐ the repo to support ongoing work.
