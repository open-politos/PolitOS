# Knowledge Base

This directory contains the versioned knowledge base that is fed to the policy engine agent. Every entry here has been approved through the governance process.

## Structure

Knowledge base entries are organized by policy domain:

```
knowledge-base/
├── economy/
├── environment/
├── education/
├── healthcare/
├── foreign-policy/
├── digital-rights/
└── ...
```

Each entry is a YAML file with:

```yaml
id: "kb-2026-001"
domain: "economy"
title: "Position on minimum wage"
content: "..."
approved_by: "GOV-2026-042"       # Governance decision ID
approved_date: "2026-03-15"
version: 1
supersedes: null
```

## Rules

- No entry may be added without a governance decision reference
- All changes are tracked via git history
- The kb-curator agent may propose new entries, but they must go through deliberation
