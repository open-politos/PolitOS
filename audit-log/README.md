# Audit Log

Append-only log of all governance decisions, AI outputs, and system events.

## Principles

1. **Append-only** — Entries are never modified or deleted
2. **Public** — Anyone can read the full audit trail
3. **Timestamped** — Every entry has a verifiable timestamp
4. **Traceable** — Every AI output links back to the governance decisions that authorized it

## Entry Format

```yaml
id: "LOG-2026-00001"
timestamp: "2026-03-15T14:30:00Z"
type: "governance_decision"        # governance_decision | ai_output | member_action | system_event
actor: "governance/voting-rules"
description: "Proposal GOV-2026-042 passed with 73% approval"
references:
  - "GOV-2026-042"
hash: "sha256:..."                 # Hash of the entry for integrity verification
previous_hash: "sha256:..."        # Hash chain for tamper detection
```

## Storage

Configure storage backend in `config/party.config.yaml`:
- `local` — File-based storage (default)
- `s3` — Cloud storage
- `ipfs` — Distributed storage for maximum tamper resistance
