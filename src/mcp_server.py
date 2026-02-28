"""PolitOS MCP Server — exposes core functions as MCP tools via stdio."""

import re
from dataclasses import asdict
from pathlib import Path

import yaml
from mcp.server.fastmcp import FastMCP

from src.core.config import PROJECT_ROOT

mcp = FastMCP(
    "PolitOS",
    instructions=(
        "PolitOS is an AI-governed political organization runtime. "
        "Use these tools to interact with its knowledge base, governance system, "
        "audit log, and constitutional framework."
    ),
)


def _extract_sources(text: str) -> list[str]:
    """Extract [KB: ...], [GOV: ...], [CONST: ...] citations from response text."""
    pattern = r"\[(KB|GOV|CONST):\s*([^\]]+)\]"
    return [f"{m[0]}:{m[1].strip()}" for m in re.findall(pattern, text)]


@mcp.tool()
def politos_chat(message: str) -> dict:
    """Ask the PolitOS Representative Agent a question as a citizen.

    The agent searches the knowledge base, responds with cited sources,
    and validates the response against the constitution.

    Args:
        message: The citizen's question or message.

    Returns:
        Response with sources and audit ID.
    """
    from src.agents.crew import run_chat
    from src.core.audit import log

    result = run_chat(message)
    response_text = result["response"]
    sources = _extract_sources(response_text)

    audit_entry = log(
        type="citizen_interaction",
        topic=message[:100],
        sources=sources if sources else ["no_sources"],
    )

    return {
        "response": response_text,
        "sources": sources,
        "audit_id": audit_entry.id,
    }


@mcp.tool()
def politos_search_knowledge(query: str, n_results: int = 5) -> list[dict]:
    """Search the PolitOS knowledge base by semantic similarity.

    Args:
        query: Search query (e.g. "climate policy", "education reform").
        n_results: Max number of results to return (default 5).

    Returns:
        List of matching knowledge base entries with id, domain, title, content.
    """
    from src.core.kb import search

    entries = search(query, n_results=n_results)
    return [asdict(e) for e in entries]


@mcp.tool()
def politos_list_topics() -> list[str]:
    """List all topic titles in the PolitOS knowledge base.

    Returns:
        List of topic title strings.
    """
    from src.core.kb import list_topics

    return list_topics()


@mcp.tool()
def politos_submit_proposal(
    title: str,
    description: str,
    rationale: str,
    affected_domains: list[str],
) -> dict:
    """Submit a governance proposal to PolitOS.

    Runs the full proposal workflow: compliance check against the constitution,
    advocate counter-arguments, and a citizen-facing summary.
    The proposal is saved and logged in the audit trail.

    Args:
        title: Proposal title.
        description: What the proposal does.
        rationale: Why this proposal is needed.
        affected_domains: Policy domains affected (e.g. ["environment", "economy"]).

    Returns:
        Proposal ID, compliance result, counter-arguments, and summary.
    """
    import uuid

    from src.agents.crew import run_proposal_workflow
    from src.core.audit import log

    proposal_id = f"PROP-{uuid.uuid4().hex[:6].upper()}"

    result = run_proposal_workflow(
        title=title,
        description=description,
        rationale=rationale,
        affected_domains=affected_domains,
    )

    # Write proposal to filesystem
    proposals_dir = PROJECT_ROOT / "governance" / "proposals"
    proposals_dir.mkdir(parents=True, exist_ok=True)

    proposal_data = {
        "id": proposal_id,
        "status": "review",
        "title": title,
        "description": description,
        "rationale": rationale,
        "affected_domains": affected_domains,
        "compliance": result["compliance"],
        "counter_arguments": result["counter_arguments"],
        "summary": result["summary"],
    }
    proposal_path = proposals_dir / f"{proposal_id}.yaml"
    proposal_path.write_text(
        yaml.dump(proposal_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    )

    log(
        type="proposal_submitted",
        topic=title,
        sources=[f"GOV:{proposal_id}"],
    )

    return {
        "id": proposal_id,
        "status": "review",
        "compliance": result["compliance"],
        "counter_arguments": result["counter_arguments"],
        "summary": result["summary"],
    }


@mcp.tool()
def politos_get_proposal(proposal_id: str) -> dict:
    """Get a governance proposal by its ID.

    Args:
        proposal_id: The proposal ID (e.g. "PROP-A1B2C3").

    Returns:
        Full proposal data including compliance and counter-arguments.
    """
    proposal_path = PROJECT_ROOT / "governance" / "proposals" / f"{proposal_id}.yaml"
    if not proposal_path.exists():
        return {"error": f"Proposal {proposal_id} not found"}
    return yaml.safe_load(proposal_path.read_text())


@mcp.tool()
def politos_audit_log(
    type: str | None = None,
    after: str | None = None,
    before: str | None = None,
) -> list[dict]:
    """Query the PolitOS audit log.

    Args:
        type: Filter by entry type (e.g. "citizen_interaction", "proposal_submitted").
        after: Only entries after this ISO timestamp.
        before: Only entries before this ISO timestamp.

    Returns:
        List of audit log entries.
    """
    from src.core.audit import query

    entries = query(type=type, after=after, before=before)
    return [asdict(e) for e in entries]


@mcp.tool()
def politos_validate(statement: str) -> dict:
    """Validate a statement against the PolitOS constitution.

    Checks the statement against core principles, ethical boundaries,
    and legal constraints using LLM-based analysis.

    Args:
        statement: The statement to validate.

    Returns:
        Validation result with valid flag, violations, and sources.
    """
    from src.core.constitution import validate

    result = validate(statement)
    return {
        "valid": result.valid,
        "violations": [asdict(v) for v in result.violations],
        "sources": result.sources,
    }


def main():
    """Run the PolitOS MCP server (stdio transport)."""
    from src.core.kb import index_knowledge_base

    index_knowledge_base()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
