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


@mcp.tool()
def politos_setup_status() -> dict:
    """Check the founding status of this PolitOS organization.

    Returns which setup steps are complete, the current config (if any),
    and available policy domains for knowledge base seeding.

    Returns:
        Step completion map, current config, and domain list.
    """
    from src.core.setup import get_setup_status, get_domains

    status = get_setup_status()
    status["domains"] = get_domains()
    return status


@mcp.tool()
def politos_setup_identity(
    name: str,
    short_name: str,
    language: str,
    jurisdiction: str,
    voting_method: str = "approval",
    standard_quorum: float = 0.1,
    standard_threshold: float = 0.6,
    website: str | None = None,
) -> dict:
    """Set up the organization identity (Step 1 of founding).

    Creates config/party.config.yaml with the organization's basic info.

    Args:
        name: Full organization name (e.g. "Citizens for Digital Democracy").
        short_name: Abbreviation (e.g. "CDD").
        language: Primary language ISO 639-1 code (e.g. "en", "de").
        jurisdiction: Country ISO 3166-1 alpha-2 code (e.g. "DE", "US").
        voting_method: "approval", "ranked-choice", or "simple-majority".
        standard_quorum: Min participation ratio (0.05–1.0, default 0.1).
        standard_threshold: Approval ratio to pass (0.5–1.0, default 0.6).
        website: Optional website URL.

    Returns:
        Written config or error.
    """
    from src.core.setup import write_identity

    return write_identity({
        "name": name,
        "short_name": short_name,
        "language": language,
        "jurisdiction": jurisdiction,
        "website": website,
        "voting_method": voting_method,
        "standard_quorum": standard_quorum,
        "standard_threshold": standard_threshold,
    })


@mcp.tool()
def politos_setup_constitution(
    custom_principles: list[dict] | None = None,
    custom_boundaries: list[dict] | None = None,
    custom_constraints: list[dict] | None = None,
) -> dict:
    """Review or extend the constitution (Step 2 of founding).

    Call with no arguments to read the current constitution.
    Pass custom rules to append them (immutable: false). Default rules
    cannot be removed.

    Args:
        custom_principles: List of {name, statement} to add as principles.
        custom_boundaries: List of {name, description, severity?} to add.
        custom_constraints: List of {name, description, applies_to?} to add.

    Returns:
        Current constitution (read-only mode) or added rules summary.
    """
    from src.core.setup import add_constitutional_rules

    return add_constitutional_rules(
        principles=custom_principles,
        boundaries=custom_boundaries,
        constraints=custom_constraints,
    )


@mcp.tool()
def politos_setup_persona(
    name: str,
    tone: str,
    language_level: str = "accessible to general public",
    formality: str = "professional but approachable",
    fallback_response: str | None = None,
) -> dict:
    """Configure the representative agent persona (Step 3 of founding).

    Args:
        name: Name of the AI representative (e.g. "Ada", "Vox").
        tone: Communication tone (e.g. "passionate but measured").
        language_level: Target audience level (default: general public).
        formality: Formality level (default: professional but approachable).
        fallback_response: What to say on undecided topics (optional, has default).

    Returns:
        Written persona config.
    """
    from src.core.setup import write_persona

    fields: dict = {
        "name": name,
        "tone": tone,
        "language_level": language_level,
        "formality": formality,
    }
    if fallback_response is not None:
        fields["fallback_response"] = fallback_response
    return write_persona(fields)


@mcp.tool()
def politos_setup_seed_kb(
    domain: str,
    title: str,
    content: str,
    entry_id: str | None = None,
    topic_hint: str | None = None,
) -> dict:
    """Add a knowledge base entry during founding (Step 4).

    Each call creates one policy position. Call multiple times to seed
    positions across domains. Use politos_setup_status to see available domains.

    Args:
        domain: Policy domain (e.g. "economy", "environment", "digital-rights").
        title: Clear title for the position (e.g. "Position on minimum wage").
        content: Full policy position text.
        entry_id: Optional custom ID (auto-generated as kb-YYYY-NNN if omitted).
        topic_hint: Optional filename hint (derived from title if omitted).

    Returns:
        Created entry with ID and file path.
    """
    from src.core.setup import write_kb_entry

    return write_kb_entry(
        domain=domain,
        title=title,
        content=content,
        entry_id=entry_id,
        topic_hint=topic_hint,
    )


@mcp.tool()
def politos_setup_complete(
    discard_entry_ids: list[str] | None = None,
) -> dict:
    """Finalize the founding process (Steps 5+6).

    Validates all KB entries against the constitution. If all pass,
    creates the founding resolution and audit log entry.

    Args:
        discard_entry_ids: Optional list of KB entry IDs to delete before validation.

    Returns:
        Validation results. If all valid, also returns founding summary.
        If violations found, returns them without creating the report —
        fix entries and call again.
    """
    from src.core.setup import (
        get_setup_status,
        validate_all_kb_entries,
        create_founding_report,
    )
    from src.core.kb import index_knowledge_base, load_all_entries

    # Check step 1 is done
    status = get_setup_status()
    if not status["steps"]["1_identity"]["complete"]:
        return {"error": "Step 1 (Organization Identity) must be completed first. Use politos_setup_identity."}

    # Discard entries if requested
    if discard_entry_ids:
        kb_dir = PROJECT_ROOT / "knowledge-base"
        for entry_id in discard_entry_ids:
            for path in kb_dir.rglob("*.yaml"):
                if path.name == "README.md":
                    continue
                try:
                    data = yaml.safe_load(path.read_text())
                    if isinstance(data, dict) and data.get("id") == entry_id:
                        path.unlink()
                        break
                except (yaml.YAMLError, UnicodeDecodeError):
                    continue

    # Validate
    validation = validate_all_kb_entries()
    if not validation["all_valid"]:
        return {
            "status": "violations_found",
            "validation": validation,
            "message": "Fix or discard violating entries, then call politos_setup_complete again.",
        }

    # Create founding report
    report = create_founding_report()

    # Rebuild ChromaDB index if there are entries
    entries = load_all_entries()
    if entries:
        index_knowledge_base()

    return {
        "status": "complete",
        "validation": validation,
        "founding_summary": report,
    }


def main():
    """Run the PolitOS MCP server (stdio transport)."""
    from src.core.kb import index_knowledge_base, load_all_entries

    # Only index if there are KB entries (avoid unnecessary ChromaDB init during clean setup)
    if load_all_entries():
        index_knowledge_base()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
