# Compliance Agent

Validates all outputs and proposals against the constitution layer.

## Responsibilities

- Check every proposal against `constitution/core-principles.yaml`
- Validate AI outputs against `constitution/ethical-boundaries.yaml`
- Flag potential legal issues per `constitution/legal-constraints.yaml`
- Block outputs that violate constitutional rules
- Report violations to the audit log

## Trigger Points

- Before any AI output is published
- When a new proposal is submitted
- When a governance decision is finalized
- On any change to the knowledge base
