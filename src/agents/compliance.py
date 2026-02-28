"""Compliance Agent — validates outputs and proposals against the constitution."""

from crewai import Agent
from crewai.tools import tool

from src.core.config import load_config
from src.core.constitution import Constitution, ValidationResult, load_constitution, validate


_constitution: Constitution | None = None


def _get_constitution() -> Constitution:
    global _constitution
    if _constitution is None:
        _constitution = load_constitution()
    return _constitution


@tool("validate_against_constitution")
def validate_against_constitution(statement: str) -> str:
    """Validate a statement against the PolitOS constitution.
    Returns YAML with valid (bool) and any violations found."""
    result = validate(statement, _get_constitution())
    lines = [f"valid: {result.valid}"]
    if result.violations:
        lines.append("violations:")
        for v in result.violations:
            lines.append(f"  - source: '{v.source}'")
            lines.append(f"    description: '{v.description}'")
    else:
        lines.append("violations: []")
    return "\n".join(lines)


@tool("get_constitution_rules")
def get_constitution_rules() -> str:
    """Get all constitutional rules as text for reference."""
    return _get_constitution().all_rules_text()


def create_compliance_agent() -> Agent:
    """Create the Compliance Agent."""
    cfg = load_config()
    constitution = _get_constitution()

    return Agent(
        role="Constitutional Compliance Checker",
        goal=(
            "Validate all statements, proposals, and outputs against the PolitOS constitution. "
            "Ensure nothing violates core principles, ethical boundaries, or legal constraints."
        ),
        backstory=(
            f"You are the compliance officer for {cfg.organization.name}. "
            "Your job is to check every proposal and AI output against the constitutional rules. "
            "You must be strict and thorough — if something violates the constitution, you must flag it. "
            f"Here are the rules you enforce:\n\n{constitution.all_rules_text()}"
        ),
        tools=[validate_against_constitution, get_constitution_rules],
        verbose=False,
        allow_delegation=False,
    )


def check_compliance(statement: str) -> ValidationResult:
    """Direct function to check compliance without going through CrewAI."""
    return validate(statement, _get_constitution())
