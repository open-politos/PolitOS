"""Loads constitution YAML files and provides validation."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from src.core.config import PROJECT_ROOT


@dataclass
class Violation:
    source: str  # e.g. "CONST:no_violence"
    description: str


@dataclass
class ValidationResult:
    valid: bool
    violations: list[Violation] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


@dataclass
class Constitution:
    principles: dict[str, dict]
    boundaries: dict[str, dict]
    constraints: dict[str, dict]

    def all_rules_text(self) -> str:
        """Return a combined text description of all constitutional rules."""
        lines: list[str] = []
        lines.append("## Core Principles")
        for name, p in self.principles.items():
            lines.append(f"- {name}: {p['statement']}")
        lines.append("\n## Ethical Boundaries")
        for name, b in self.boundaries.items():
            lines.append(f"- {name} (severity: {b.get('severity', 'high')}): {b['description']}")
        lines.append("\n## Legal Constraints")
        for name, c in self.constraints.items():
            lines.append(f"- {name}: {c['description']}")
        return "\n".join(lines)


def load_constitution(root: Path | None = None) -> Constitution:
    """Load all constitution YAML files."""
    root = root or PROJECT_ROOT
    constitution_dir = root / "constitution"

    principles_data = yaml.safe_load(
        (constitution_dir / "core-principles.yaml").read_text()
    )
    boundaries_data = yaml.safe_load(
        (constitution_dir / "ethical-boundaries.yaml").read_text()
    )
    constraints_data = yaml.safe_load(
        (constitution_dir / "legal-constraints.yaml").read_text()
    )

    return Constitution(
        principles=principles_data.get("principles", {}),
        boundaries=boundaries_data.get("boundaries", {}),
        constraints=constraints_data.get("constraints", {}),
    )


def validate(statement: str, constitution: Constitution | None = None) -> ValidationResult:
    """Validate a statement against the constitution.

    Uses LLM to check the statement against all constitutional rules.
    Returns a ValidationResult with any violations found.
    """
    if constitution is None:
        constitution = load_constitution()

    from src.core.llm import completion

    rules_text = constitution.all_rules_text()

    messages = [
        {
            "role": "system",
            "content": (
                "You are a constitutional compliance checker. "
                "You will be given a set of constitutional rules and a statement to validate. "
                "Check if the statement violates any rule. "
                "Respond in YAML format with:\n"
                "valid: true/false\n"
                "violations:\n"
                "  - source: 'CONST:rule_name'\n"
                "    description: 'explanation'\n"
                "If no violations, respond with:\n"
                "valid: true\n"
                "violations: []\n"
                "Only output the YAML, nothing else."
            ),
        },
        {
            "role": "user",
            "content": (
                f"## Constitutional Rules\n{rules_text}\n\n"
                f"## Statement to Validate\n{statement}"
            ),
        },
    ]

    response_text = completion(messages, temperature=0.1)

    # Strip markdown code fences if present
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]  # remove opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    try:
        result = yaml.safe_load(cleaned)
    except yaml.YAMLError:
        # If LLM output isn't parseable, treat as valid (fail-open for now, log it)
        return ValidationResult(valid=True, sources=["CONST:parse_error"])

    violations = []
    for v in result.get("violations", []) or []:
        violations.append(Violation(source=v.get("source", "CONST:unknown"), description=v.get("description", "")))

    sources = [v.source for v in violations] if violations else ["CONST:compliant"]

    return ValidationResult(
        valid=result.get("valid", True),
        violations=violations,
        sources=sources,
    )
