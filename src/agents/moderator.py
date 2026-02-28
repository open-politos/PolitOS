"""Moderator Agent — manages deliberation lifecycle."""

from pathlib import Path

import yaml
from crewai import Agent

from src.core.config import PROJECT_ROOT, get_crewai_llm_model, load_config


def _load_deliberation_protocol(root: Path | None = None) -> dict:
    root = root or PROJECT_ROOT
    path = root / "governance" / "deliberation-protocol.yaml"
    return yaml.safe_load(path.read_text()) if path.exists() else {}


def _load_voting_rules(root: Path | None = None) -> dict:
    root = root or PROJECT_ROOT
    path = root / "governance" / "voting-rules.yaml"
    return yaml.safe_load(path.read_text()) if path.exists() else {}


def create_moderator_agent() -> Agent:
    """Create the Moderator Agent."""
    cfg = load_config()
    protocol = _load_deliberation_protocol()
    voting = _load_voting_rules()

    phases_text = ""
    for phase_key, phase in (protocol.get("phases") or {}).items():
        phases_text += f"\n### {phase_key}: {phase.get('description', '')}\n"

    voting_text = yaml.dump(voting.get("defaults", {}), default_flow_style=False)

    return Agent(
        role="Governance Moderator",
        goal=(
            "Track proposal lifecycle phases. Enforce deliberation timelines and rules. "
            "Ensure quorum requirements are met. Manage the governance process."
        ),
        backstory=(
            f"You are the governance moderator for {cfg.organization.name}. "
            "You ensure all governance processes follow the rules.\n\n"
            f"## Deliberation Phases\n{phases_text}\n"
            f"## Voting Rules\n{voting_text}\n"
            "Your responsibilities:\n"
            "- Track proposal lifecycle phases\n"
            "- Enforce deliberation timelines\n"
            "- Notify when phase transitions should happen\n"
            "- Ensure quorum requirements are met\n"
            "- Manage sortition panel selection when needed"
        ),
        llm=get_crewai_llm_model(cfg),
        verbose=False,
        allow_delegation=False,
    )
