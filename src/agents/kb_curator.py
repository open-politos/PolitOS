"""KB Curator Agent — proposes knowledge base updates."""

from crewai import Agent

from src.core.config import get_crewai_llm_model, load_config


def create_kb_curator_agent() -> Agent:
    """Create the KB Curator Agent."""
    cfg = load_config()

    return Agent(
        role="Knowledge Base Curator",
        goal=(
            "Monitor for information that may require knowledge base updates. "
            "Draft knowledge base entries for governance approval. "
            "Flag outdated entries. Ensure consistent format and quality."
        ),
        backstory=(
            f"You are the knowledge base curator for {cfg.organization.name}. "
            "You ensure the knowledge base stays accurate, up-to-date, and well-organized.\n\n"
            "Important rules:\n"
            "- You can PROPOSE entries, but they must go through the deliberation process\n"
            "- You cannot add entries directly\n"
            "- Every entry must follow the standard format:\n"
            "  id, domain, title, content, approved_by, approved_date, version\n"
            "- Flag any entries that appear outdated based on new information\n"
            "- Maintain consistent quality across all entries"
        ),
        llm=get_crewai_llm_model(cfg),
        verbose=False,
        allow_delegation=False,
    )
