"""GET /audit — public audit log access."""

from fastapi import APIRouter
from pydantic import BaseModel

from src.core.audit import AuditEntry, query

router = APIRouter()


class AuditEntryResponse(BaseModel):
    id: str
    timestamp: str
    type: str
    topic: str
    sources_cited: list[str]
    escalation: str | None = None
    entry_hash: str | None = None


@router.get("/audit")
async def get_audit_log(
    type: str | None = None,
    after: str | None = None,
    before: str | None = None,
) -> list[AuditEntryResponse]:
    """Query the public audit log."""
    entries = query(type=type, after=after, before=before)
    return [
        AuditEntryResponse(
            id=e.id,
            timestamp=e.timestamp,
            type=e.type,
            topic=e.topic,
            sources_cited=e.sources_cited,
            escalation=e.escalation,
            entry_hash=e.entry_hash,
        )
        for e in entries
    ]
