"""GET /knowledge/search, GET /knowledge/topics — read-only KB access."""

from fastapi import APIRouter
from pydantic import BaseModel

from src.core.kb import KBEntry, list_topics, search

router = APIRouter()


class KBSearchResult(BaseModel):
    id: str
    domain: str
    title: str
    content: str
    approved_by: str | None = None
    approved_date: str | None = None


@router.get("/knowledge/search")
async def search_knowledge(q: str, n: int = 5) -> list[KBSearchResult]:
    """Search the knowledge base by query."""
    results = search(q, n_results=n)
    return [
        KBSearchResult(
            id=e.id,
            domain=e.domain,
            title=e.title,
            content=e.content,
            approved_by=e.approved_by,
            approved_date=e.approved_date,
        )
        for e in results
    ]


@router.get("/knowledge/topics")
async def get_topics() -> list[str]:
    """List all topics in the knowledge base."""
    return list_topics()
