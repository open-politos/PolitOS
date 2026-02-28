"""POST /proposals, GET /proposals/{id} — governance proposals."""

import uuid
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.agents.crew import run_proposal_workflow
from src.core.audit import log
from src.core.config import PROJECT_ROOT

router = APIRouter()


class ProposalRequest(BaseModel):
    title: str
    description: str
    rationale: str
    affected_domains: list[str]


class ProposalResponse(BaseModel):
    id: str
    status: str
    compliance: str
    counter_arguments: str
    summary: str


def _proposals_dir() -> Path:
    d = PROJECT_ROOT / "governance" / "proposals"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _generate_proposal_id() -> str:
    return f"PROP-{uuid.uuid4().hex[:6].upper()}"


@router.post("/proposals")
async def create_proposal(request: ProposalRequest) -> ProposalResponse:
    """Submit a new proposal. Runs compliance check and advocate analysis."""
    proposal_id = _generate_proposal_id()

    result = run_proposal_workflow(
        title=request.title,
        description=request.description,
        rationale=request.rationale,
        affected_domains=request.affected_domains,
    )

    # Write proposal to filesystem
    proposal_data = {
        "id": proposal_id,
        "status": "review",
        "title": request.title,
        "description": request.description,
        "rationale": request.rationale,
        "affected_domains": request.affected_domains,
        "compliance": result["compliance"],
        "counter_arguments": result["counter_arguments"],
        "summary": result["summary"],
    }
    proposal_path = _proposals_dir() / f"{proposal_id}.yaml"
    proposal_path.write_text(yaml.dump(proposal_data, default_flow_style=False, allow_unicode=True, sort_keys=False))

    log(
        type="proposal_submitted",
        topic=request.title,
        sources=[f"GOV:{proposal_id}"],
    )

    return ProposalResponse(
        id=proposal_id,
        status="review",
        compliance=result["compliance"],
        counter_arguments=result["counter_arguments"],
        summary=result["summary"],
    )


@router.get("/proposals/{proposal_id}")
async def get_proposal(proposal_id: str) -> dict:
    """Get a proposal by ID."""
    proposal_path = _proposals_dir() / f"{proposal_id}.yaml"
    if not proposal_path.exists():
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")
    return yaml.safe_load(proposal_path.read_text())
