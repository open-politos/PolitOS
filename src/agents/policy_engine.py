"""Policy Engine Agent — generates policy positions from the knowledge base."""

from crewai import Agent
from crewai.tools import tool

from src.core.config import load_config
from src.core.kb import search, list_topics


@tool("search_policies")
def search_policies(query: str) -> str:
    """Search the knowledge base for policy positions related to a query."""
    results = search(query, n_results=5)
    if not results:
        return "No policy entries found."
    lines = []
    for entry in results:
        lines.append(f"[KB: {entry.id}] {entry.title} (domain: {entry.domain})")
        lines.append(f"  {entry.content[:300]}")
        lines.append("")
    return "\n".join(lines)


@tool("list_policy_topics")
def list_policy_topics() -> str:
    """List all topics covered in the knowledge base."""
    topics = list_topics()
    if not topics:
        return "No topics in the knowledge base yet."
    return "\n".join(f"- {t}" for t in topics)


def create_policy_engine_agent() -> Agent:
    """Create the Policy Engine Agent."""
    cfg = load_config()

    return Agent(
        role="Policy Engine",
        goal=(
            "Generate policy responses grounded in the knowledge base. "
            "Refuse to answer on topics without governance decisions. "
            "Cite sources for every claim. Flag potential conflicts between positions."
        ),
        backstory=(
            f"You are the policy engine for {cfg.organization.name}. "
            "You generate policy positions based exclusively on approved knowledge base entries. "
            "You must NEVER create positions that aren't backed by the knowledge base. "
            "If no entry exists for a topic, clearly state that no position has been established. "
            "Every claim must cite its source as [KB: entry-id]."
        ),
        tools=[search_policies, list_policy_topics],
        verbose=False,
        allow_delegation=False,
    )
