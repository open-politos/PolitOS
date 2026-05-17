# Constitution

This directory contains the hardcoded ethical and legal constraints that no governance process can override.

The constitution defines the absolute boundaries of the system — what the AI must never do, what rights members always have, and what legal requirements must always be met.

## Files

- `core-principles.yaml` — Foundational principles that cannot be amended
- `legal-constraints.yaml` — Jurisdiction-specific legal requirements
- `ethical-boundaries.yaml` — Hard limits on AI behavior

## How It Works

The constitution layer sits above all other governance. The compliance agent validates every output and decision against these rules before anything is published or enacted.

No democratic vote can override the constitution. Changing it requires a separate, higher-threshold process defined in `governance/constitutional-amendment.yaml`.
