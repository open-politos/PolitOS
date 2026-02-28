"""Append-only YAML audit logger with hash chain."""

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

from src.core.config import PROJECT_ROOT

AUDIT_FILE = "audit-log/interactions.yaml"


@dataclass
class AuditEntry:
    id: str
    timestamp: str
    type: str
    topic: str
    sources_cited: list[str] = field(default_factory=list)
    escalation: str | None = None
    previous_hash: str | None = None
    entry_hash: str | None = None


def _compute_hash(entry: dict) -> str:
    """Compute SHA-256 hash of an audit entry (excluding its own hash)."""
    hashable = {k: v for k, v in entry.items() if k != "entry_hash"}
    content = yaml.dump(hashable, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _load_entries(root: Path | None = None) -> list[dict]:
    """Load existing audit entries from file."""
    root = root or PROJECT_ROOT
    path = root / AUDIT_FILE
    if not path.exists():
        return []
    content = path.read_text()
    if not content.strip():
        return []
    entries = yaml.safe_load(content)
    return entries if isinstance(entries, list) else []


def _save_entries(entries: list[dict], root: Path | None = None) -> None:
    """Write all entries back to the audit file."""
    root = root or PROJECT_ROOT
    path = root / AUDIT_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(entries, default_flow_style=False, allow_unicode=True, sort_keys=False))


def log(
    type: str,
    topic: str,
    sources: list[str],
    escalation: str | None = None,
    root: Path | None = None,
) -> AuditEntry:
    """Append an audit entry. Returns the created entry."""
    root = root or PROJECT_ROOT
    existing = _load_entries(root)

    # Get previous hash for chain
    previous_hash = None
    if existing:
        last = existing[-1]
        previous_hash = last.get("entry_hash") or _compute_hash(last)

    entry_id = f"AUDIT-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    entry_dict = {
        "id": entry_id,
        "timestamp": timestamp,
        "type": type,
        "topic": topic,
        "sources_cited": sources,
        "escalation": escalation,
        "previous_hash": previous_hash,
    }
    entry_dict["entry_hash"] = _compute_hash(entry_dict)

    existing.append(entry_dict)
    _save_entries(existing, root)

    return AuditEntry(**entry_dict)


def query(
    type: str | None = None,
    after: str | None = None,
    before: str | None = None,
    root: Path | None = None,
) -> list[AuditEntry]:
    """Query the audit log with optional filters."""
    entries = _load_entries(root)
    results = []

    for e in entries:
        if type and e.get("type") != type:
            continue
        ts = e.get("timestamp", "")
        if after and ts < after:
            continue
        if before and ts > before:
            continue
        results.append(
            AuditEntry(
                id=e.get("id", ""),
                timestamp=ts,
                type=e.get("type", ""),
                topic=e.get("topic", ""),
                sources_cited=e.get("sources_cited", []),
                escalation=e.get("escalation"),
                previous_hash=e.get("previous_hash"),
                entry_hash=e.get("entry_hash"),
            )
        )

    return results
