"""POST /chat — citizen interacts with the Representative Agent."""

import re

from fastapi import APIRouter
from pydantic import BaseModel

from src.agents.crew import run_chat
from src.core.audit import log

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    sources: list[str]
    audit_id: str


def _extract_sources(text: str) -> list[str]:
    """Extract [KB: ...], [GOV: ...], [CONST: ...] citations from response text."""
    pattern = r"\[(KB|GOV|CONST):\s*([^\]]+)\]"
    return [f"{m[0]}:{m[1].strip()}" for m in re.findall(pattern, text)]


@router.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """Citizen sends a message, Representative Agent responds."""
    result = run_chat(request.message)

    response_text = result["response"]
    sources = _extract_sources(response_text)

    audit_entry = log(
        type="citizen_interaction",
        topic=request.message[:100],
        sources=sources if sources else ["no_sources"],
    )

    return ChatResponse(
        response=response_text,
        sources=sources,
        audit_id=audit_entry.id,
    )
