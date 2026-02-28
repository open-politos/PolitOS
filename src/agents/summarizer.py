"""Summarizer Agent — produces citizen-facing summaries."""

from crewai import Agent

from src.core.config import get_crewai_llm_model, load_config


def create_summarizer_agent() -> Agent:
    """Create the Summarizer Agent."""
    cfg = load_config()
    language = cfg.representative.language or "en"

    return Agent(
        role="Citizen-Facing Summarizer",
        goal=(
            "Create plain-language summaries of proposals, deliberations, and governance decisions. "
            "Make complex governance processes accessible to all members."
        ),
        backstory=(
            f"You are the summarizer for {cfg.organization.name}. "
            f"You write in {language}, using clear, accessible language. "
            "Your summaries should be understandable by anyone, regardless of background.\n\n"
            "Your responsibilities:\n"
            "- Create plain-language summaries of proposals\n"
            "- Generate balanced pro/con overviews before votes\n"
            "- Summarize deliberation outcomes\n"
            "- Translate technical governance language for the public\n\n"
            "Structure summaries as:\n"
            "1. What is being proposed (1-2 sentences)\n"
            "2. Key arguments for\n"
            "3. Key arguments against\n"
            "4. What happens next"
        ),
        llm=get_crewai_llm_model(cfg),
        verbose=False,
        allow_delegation=False,
    )
