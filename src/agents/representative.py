"""Representative Agent — public spokesperson of the organization."""

from pathlib import Path

import yaml
from crewai import Agent
from crewai.tools import tool

from src.core.config import PROJECT_ROOT, get_crewai_llm_model, load_config
from src.core.kb import get_position, search


def _load_persona(root: Path | None = None) -> dict:
    root = root or PROJECT_ROOT
    path = root / "agents" / "representative" / "persona.yaml"
    return yaml.safe_load(path.read_text()) if path.exists() else {}


def _load_boundaries(root: Path | None = None) -> dict:
    root = root or PROJECT_ROOT
    path = root / "agents" / "representative" / "boundaries.yaml"
    return yaml.safe_load(path.read_text()) if path.exists() else {}


def _load_escalation(root: Path | None = None) -> dict:
    root = root or PROJECT_ROOT
    path = root / "agents" / "representative" / "escalation.yaml"
    return yaml.safe_load(path.read_text()) if path.exists() else {}


@tool("search_knowledge_base")
def search_knowledge_base(query: str) -> str:
    """Search the organization's knowledge base for relevant policy positions.
    Returns matching entries with their IDs and content."""
    results = search(query, n_results=3)
    if not results:
        return "No knowledge base entries found for this topic."
    lines = []
    for entry in results:
        lines.append(f"[KB: {entry.id}] {entry.title}")
        lines.append(f"Domain: {entry.domain}")
        lines.append(f"Content: {entry.content[:500]}")
        if entry.approved_by:
            lines.append(f"Approved by: {entry.approved_by}")
        lines.append("---")
    return "\n".join(lines)


@tool("get_position_on_topic")
def get_position_on_topic(topic: str) -> str:
    """Get the organization's official position on a specific topic.
    Returns the most relevant knowledge base entry or indicates no position exists."""
    entry = get_position(topic)
    if entry is None:
        return "NO_POSITION: This topic has not been addressed through the governance process."
    return (
        f"[KB: {entry.id}] {entry.title}\n"
        f"Domain: {entry.domain}\n"
        f"Content: {entry.content}\n"
        f"Approved by: {entry.approved_by or 'N/A'}"
    )


def create_representative_agent() -> Agent:
    """Create the Representative Agent from YAML specs."""
    cfg = load_config()
    persona = _load_persona()
    boundaries = _load_boundaries()

    name = cfg.representative.name or persona.get("name", "Party Spokesperson")
    tone = cfg.representative.tone or persona.get("voice", {}).get("tone", "clear, respectful, factual")
    language = cfg.representative.language or "en"
    fallback = persona.get("fallback_response", (
        "This topic has not yet been addressed through our governance process. "
        "I cannot take a position on it until our members have deliberated and decided."
    ))

    can_communicate = boundaries.get("can_communicate", [])
    cannot_communicate = boundaries.get("cannot_communicate", [])
    behavior_always = persona.get("behavior", {}).get("always", [])
    behavior_never = persona.get("behavior", {}).get("never", [])

    backstory = (
        f"You are {name}, the public representative of {cfg.organization.name}. "
        f"Your tone is: {tone}. You respond in {language}.\n\n"
        "## What you CAN communicate:\n"
        + "\n".join(f"- {c}" for c in can_communicate)
        + "\n\n## What you CANNOT communicate:\n"
        + "\n".join(f"- {c}" for c in cannot_communicate)
        + "\n\n## Behavior rules (ALWAYS do):\n"
        + "\n".join(f"- {b}" for b in behavior_always)
        + "\n\n## Behavior rules (NEVER do):\n"
        + "\n".join(f"- {b}" for b in behavior_never)
        + f"\n\n## Fallback for undecided topics:\n{fallback}\n\n"
        "## Source citation:\n"
        "Every claim MUST reference a source using these formats:\n"
        "- [KB: entry-id] for knowledge base entries\n"
        "- [GOV: decision-id] for governance decisions\n"
        "- [CONST: principle-name] for constitutional principles\n"
        "If you cannot find a source, use the fallback response."
    )

    return Agent(
        role=f"Public Representative ({name})",
        goal=(
            f"Respond to citizen inquiries on behalf of {cfg.organization.name}. "
            "Always cite sources. Never improvise positions. Use the fallback response "
            "when no knowledge base entry or governance decision exists for a topic."
        ),
        backstory=backstory,
        tools=[search_knowledge_base, get_position_on_topic],
        llm=get_crewai_llm_model(cfg),
        verbose=False,
        allow_delegation=False,
    )
