"""PolitOS MCP Server — exposes core functions as MCP tools via stdio."""

import re
from dataclasses import asdict
from pathlib import Path

import yaml
from mcp.server.fastmcp import FastMCP

from src.core.config import PROJECT_ROOT

mcp = FastMCP(
    "PolitOS",
    instructions="""\
PolitOS is an AI-governed political organization runtime. It provides a \
constitutional framework, knowledge base, governance process, and representative \
agent for democratic organizations.

## User Roles

- **Citizen**: Ask questions about the organization's positions. \
Start with `politos_chat` or the `citizen_question` prompt. \
Read `politos://context/representative` to understand how the spokesperson behaves.
- **Member**: Submit governance proposals via `politos_submit_proposal` or the \
`submit_proposal` prompt. Read `politos://context/governance` for deliberation rules.
- **Founder**: Set up a new organization using the setup tools \
(`politos_setup_identity`, `politos_setup_constitution`, etc.) or the \
`founding_wizard` prompt. Read `politos://context/domains` for policy areas.

## Orientation

Read resources in this order for full system understanding:
1. `politos://context/project` — architecture, tool categories, data flow
2. `politos://context/status` — current org state, setup progress, KB stats
3. `politos://context/constitution` — core principles, boundaries, constraints
4. `politos://context/workflows` — step-by-step interaction patterns

## Key Constraint

Every claim must cite its source: [KB:entry-id], [GOV:decision-id], or \
[CONST:principle-name]. Never improvise policy positions.

## Quick Start

Use the prompts (`citizen_question`, `submit_proposal`, `explore_positions`, \
`founding_wizard`) for guided interactions. They include all necessary instructions.\
""",
)


def _extract_sources(text: str) -> list[str]:
    """Extract [KB: ...], [GOV: ...], [CONST: ...] citations from response text."""
    pattern = r"\[(KB|GOV|CONST):\s*([^\]]+)\]"
    return [f"{m[0]}:{m[1].strip()}" for m in re.findall(pattern, text)]


# ---------------------------------------------------------------------------
# Context Resources (7)
# ---------------------------------------------------------------------------


@mcp.resource("politos://context/project")
def resource_project() -> str:
    """Architecture overview, pillars, tool categories, and data flow diagrams."""
    return """\
# PolitOS — Project Architecture

PolitOS is an AI-governed political organization runtime. Organizations define \
their values in a constitution, build policy positions in a knowledge base, and \
make decisions through a structured governance process. An AI representative \
agent communicates positions to citizens, always citing sources.

## Five Pillars

1. **Constitution** (`constitution/`) — Immutable core principles, ethical \
boundaries, and legal constraints. Every response and proposal is validated \
against these. Cannot be changed without a supermajority vote.
2. **Knowledge Base** (`knowledge-base/`) — YAML files organized by policy \
domain (economy, environment, education, etc.). Each entry has an ID, domain, \
title, content, and approval reference. ChromaDB provides semantic search.
3. **Governance** (`governance/`) — Deliberation protocol (5 phases) and voting \
rules (3 tiers). Proposals go through compliance check, counter-arguments, \
discussion, and formal vote.
4. **Representative Agent** (`agents/representative/`) — AI spokesperson with \
configurable name, tone, and behavior rules. Grounded only in KB and governance \
decisions. Uses fallback response for undecided topics.
5. **Audit Log** (`audit-log/`) — Append-only, hash-chained YAML log of every \
interaction, proposal, and founding event.

## Tool Categories

| Category | Tools |
|----------|-------|
| Citizen interaction | `politos_chat`, `politos_search_knowledge`, `politos_list_topics` |
| Governance | `politos_submit_proposal`, `politos_get_proposal`, `politos_validate` |
| Audit | `politos_audit_log` |
| Setup (founding) | `politos_setup_status`, `politos_setup_identity`, `politos_setup_constitution`, `politos_setup_persona`, `politos_setup_seed_kb`, `politos_setup_complete` |

## Data Flow: Citizen Question

```
citizen question
  -> politos_chat
    -> search knowledge base (semantic)
    -> generate response with citations
    -> validate response against constitution
    -> log to audit trail
  <- response + [KB:id] sources + audit ID
```

## Data Flow: Proposal Submission

```
member proposal (title, description, rationale, domains)
  -> politos_submit_proposal
    -> compliance check against constitution
    -> advocate agent generates counter-arguments
    -> summarizer creates citizen-facing summary
    -> write proposal YAML to governance/proposals/
    -> log to audit trail
  <- proposal ID + compliance + counter-arguments + summary
```
"""


@mcp.resource("politos://context/constitution")
def resource_constitution() -> str:
    """Live constitutional rules — principles, boundaries, and constraints."""
    from src.core.constitution import load_constitution

    const = load_constitution()

    lines = ["# PolitOS Constitution\n"]

    lines.append("## Core Principles\n")
    for name, p in const.principles.items():
        immutable = p.get("immutable", True)
        marker = "immutable" if immutable else "mutable"
        lines.append(f"- **{name}** [{marker}]: {p['statement']}")

    lines.append("\n## Ethical Boundaries\n")
    for name, b in const.boundaries.items():
        severity = b.get("severity", "high")
        immutable = b.get("immutable", True)
        marker = "immutable" if immutable else "mutable"
        lines.append(f"- **{name}** [{marker}, severity: {severity}]: {b['description']}")

    lines.append("\n## Legal Constraints\n")
    for name, c in const.constraints.items():
        immutable = c.get("immutable", True)
        marker = "immutable" if immutable else "mutable"
        applies = c.get("applies_to", [])
        suffix = f" (applies to: {', '.join(applies)})" if applies else ""
        lines.append(f"- **{name}** [{marker}]: {c['description']}{suffix}")

    lines.append("\n---")
    lines.append("Use `politos_validate` to check any statement against these rules.")

    return "\n".join(lines)


@mcp.resource("politos://context/governance")
def resource_governance() -> str:
    """Deliberation protocol phases and voting rule tiers."""
    delib_path = PROJECT_ROOT / "governance" / "deliberation-protocol.yaml"
    voting_path = PROJECT_ROOT / "governance" / "voting-rules.yaml"

    delib = yaml.safe_load(delib_path.read_text()) if delib_path.exists() else {}
    voting = yaml.safe_load(voting_path.read_text()) if voting_path.exists() else {}

    lines = ["# PolitOS Governance\n"]

    # Deliberation phases
    lines.append("## Deliberation Protocol\n")
    for key, phase in (delib.get("phases") or {}).items():
        lines.append(f"### Phase: {key}")
        lines.append(f"{phase.get('description', '')}\n")
        if phase.get("required_fields"):
            lines.append("Required fields: " + ", ".join(phase["required_fields"]))
        if phase.get("min_duration_hours"):
            lines.append(f"Minimum duration: {phase['min_duration_hours']} hours")
        if phase.get("automated_actions"):
            lines.append("Automated actions:")
            for action in phase["automated_actions"]:
                lines.append(f"  - {action}")
        lines.append("")

    # Voting tiers
    lines.append("## Voting Rules\n")
    lines.append(f"Default method: {voting.get('voting_method', 'approval')}")
    lines.append(f"Anonymous ballots: {voting.get('anonymous_ballots', False)}\n")

    for tier, rules in (voting.get("defaults") or {}).items():
        lines.append(f"### {tier.title()} Tier")
        lines.append(f"- Quorum: {rules.get('quorum', 'N/A')}")
        lines.append(f"- Threshold: {rules.get('threshold', 'N/A')}")
        lines.append(f"- Voting period: {rules.get('voting_period_hours', 'N/A')} hours")
        lines.append(f"- Deliberation required: {rules.get('deliberation_required', 'N/A')}")
        if rules.get("min_deliberation_hours"):
            lines.append(f"- Min deliberation: {rules['min_deliberation_hours']} hours")
        if rules.get("cooling_off_hours"):
            lines.append(f"- Cooling off: {rules['cooling_off_hours']} hours")
        if rules.get("requires_justification"):
            lines.append("- Requires justification: yes")
        if rules.get("post_review_required"):
            lines.append("- Post-review under standard rules: yes")
        lines.append("")

    lines.append("---")
    lines.append("Use `politos_submit_proposal` to start a governance process.")

    return "\n".join(lines)


@mcp.resource("politos://context/domains")
def resource_domains() -> str:
    """Policy domains with descriptions, entry status, and guiding questions."""
    from src.core.setup import get_domains

    domains = get_domains()

    lines = ["# PolitOS Policy Domains\n"]
    for d in domains:
        status = "has entries" if d["has_entries"] else "empty"
        lines.append(f"## {d['display_name']} (`{d['key']}`) [{status}]")
        lines.append(f"{d['description']}\n")
        if d.get("guiding_questions"):
            lines.append("Guiding questions:")
            for q in d["guiding_questions"]:
                question = q if isinstance(q, str) else q.get("question", "")
                lines.append(f"  - {question}")
        lines.append("")

    lines.append("---")
    lines.append("Use `politos_setup_seed_kb` to add entries to a domain during founding.")

    return "\n".join(lines)


@mcp.resource("politos://context/representative")
def resource_representative() -> str:
    """Representative agent persona, boundaries, and escalation rules."""
    rep_dir = PROJECT_ROOT / "agents" / "representative"

    lines = ["# PolitOS Representative Agent\n"]

    # Persona
    persona_path = rep_dir / "persona.yaml"
    if persona_path.exists():
        persona = yaml.safe_load(persona_path.read_text()) or {}
        lines.append("## Persona\n")
        lines.append(f"- **Name**: {persona.get('name', 'N/A')}")
        lines.append(f"- **Role**: {persona.get('role', 'N/A')}")
        voice = persona.get("voice", {})
        lines.append(f"- **Tone**: {voice.get('tone', 'N/A')}")
        lines.append(f"- **Language level**: {voice.get('language_level', 'N/A')}")
        lines.append(f"- **Formality**: {voice.get('formality', 'N/A')}")

        if persona.get("behavior"):
            behavior = persona["behavior"]
            if behavior.get("always"):
                lines.append("\nAlways:")
                for rule in behavior["always"]:
                    lines.append(f"  - {rule}")
            if behavior.get("never"):
                lines.append("\nNever:")
                for rule in behavior["never"]:
                    lines.append(f"  - {rule}")

        if persona.get("fallback_response"):
            lines.append(f"\n**Fallback response** (used for undecided topics):\n> {persona['fallback_response'].strip()}")
        lines.append("")

    # Boundaries
    boundaries_path = rep_dir / "boundaries.yaml"
    if boundaries_path.exists():
        boundaries = yaml.safe_load(boundaries_path.read_text()) or {}
        lines.append("## Communication Boundaries\n")
        if boundaries.get("can_communicate"):
            lines.append("Can communicate:")
            for item in boundaries["can_communicate"]:
                lines.append(f"  - {item}")
        if boundaries.get("cannot_communicate"):
            lines.append("\nCannot communicate:")
            for item in boundaries["cannot_communicate"]:
                lines.append(f"  - {item}")
        src_req = boundaries.get("source_requirements", {})
        if src_req:
            lines.append(f"\nSource requirement: every claim must reference "
                         f"{', '.join(src_req.get('every_claim_must_reference', []))}.")
            lines.append(f"Unsourced claims: {src_req.get('unsourced_claims', 'blocked')}")
        lines.append("")

    # Escalation
    escalation_path = rep_dir / "escalation.yaml"
    if escalation_path.exists():
        escalation = yaml.safe_load(escalation_path.read_text()) or {}
        lines.append("## Escalation Triggers\n")
        for name, trigger in (escalation.get("triggers") or {}).items():
            lines.append(f"### {name}")
            lines.append(f"{trigger.get('description', '')}")
            if trigger.get("threshold"):
                lines.append(f"Threshold: {trigger['threshold']}")
            lines.append(f"Action: {trigger.get('action', 'N/A')}\n")

    return "\n".join(lines)


@mcp.resource("politos://context/workflows")
def resource_workflows() -> str:
    """Workflow diagrams, tool dependencies, and founding step sequence."""
    return """\
# PolitOS Workflows

## Workflow 1: Citizen Question

```
1. Client sends question
2. politos_chat:
   a. Searches KB (semantic similarity)
   b. Generates response grounded in KB entries
   c. Validates response against constitution
   d. Logs interaction to audit trail
3. Returns: response text + source citations + audit ID
```

If no KB entry matches: representative uses fallback response from persona config.

## Workflow 2: Proposal Submission

```
1. Member provides: title, description, rationale, affected_domains
2. politos_submit_proposal:
   a. Compliance agent checks against constitution
   b. Advocate agent generates counter-arguments
   c. Summarizer produces citizen-facing summary
   d. Writes proposal YAML to governance/proposals/
   e. Logs submission to audit trail
3. Returns: proposal ID + compliance result + counter-arguments + summary
```

After submission, the proposal enters the 5-phase deliberation protocol \
(see `politos://context/governance`).

## Workflow 3: Constitutional Validation

```
1. Any statement or KB entry content
2. politos_validate:
   a. Loads all principles, boundaries, constraints
   b. LLM checks statement against each rule
   c. Returns: valid/invalid + list of violations with CONST: references
```

Used automatically during founding (Step 5) and proposal submission.

## Workflow 4: Founding Sequence

```
Step 1 — Identity:        politos_setup_identity -> config/party.config.yaml
Step 2 — Constitution:    politos_setup_constitution -> constitution/*.yaml
Step 3 — Representative:  politos_setup_persona -> agents/representative/persona.yaml
Step 4 — Knowledge Base:  politos_setup_seed_kb (repeated) -> knowledge-base/{domain}/*.yaml
Step 5 — Validation:      politos_setup_complete -> validates all KB entries
Step 6 — Founding Report: politos_setup_complete -> governance/decisions/FOUNDING-001.yaml
```

Steps 5 and 6 are combined in `politos_setup_complete`. If validation fails, \
fix or discard entries and call again.

## Tool Dependency Table

| Tool | Requires Setup? | Reads | Writes |
|------|----------------|-------|--------|
| `politos_chat` | Yes (KB + config) | knowledge-base/, constitution/ | audit-log/ |
| `politos_search_knowledge` | Yes (KB) | knowledge-base/ (via ChromaDB) | — |
| `politos_list_topics` | Yes (KB) | knowledge-base/ (via ChromaDB) | — |
| `politos_submit_proposal` | Yes (config) | constitution/ | governance/proposals/, audit-log/ |
| `politos_get_proposal` | No | governance/proposals/ | — |
| `politos_validate` | No | constitution/ | — |
| `politos_audit_log` | No | audit-log/ | — |
| `politos_setup_status` | No | config/, agents/, knowledge-base/, governance/ | — |
| `politos_setup_identity` | No | config/party.config.example.yaml | config/party.config.yaml |
| `politos_setup_constitution` | No | constitution/ | constitution/ |
| `politos_setup_persona` | No | agents/representative/persona.yaml | agents/representative/persona.yaml, config/ |
| `politos_setup_seed_kb` | No | knowledge-base/ | knowledge-base/{domain}/ |
| `politos_setup_complete` | Yes (Step 1) | knowledge-base/, constitution/ | governance/decisions/, audit-log/ |
"""


@mcp.resource("politos://context/status")
def resource_status() -> str:
    """Live system status — org info, setup progress, KB and audit stats."""
    from src.core.setup import get_setup_status
    from src.core.kb import load_all_entries
    from src.core.audit import query as audit_query

    status = get_setup_status()
    entries = load_all_entries()
    audit_entries = audit_query()

    lines = ["# PolitOS System Status\n"]

    # Organization info
    if status.get("current_config"):
        cfg = status["current_config"]
        lines.append("## Organization\n")
        lines.append(f"- **Name**: {cfg.get('name', 'N/A')}")
        lines.append(f"- **Language**: {cfg.get('language', 'N/A')}")
        lines.append(f"- **Jurisdiction**: {cfg.get('jurisdiction', 'N/A')}")
        lines.append(f"- **Founded**: {cfg.get('founded', 'N/A')}")
        lines.append("")
    else:
        lines.append("## Organization\n")
        lines.append("Not yet configured. Run the founding wizard.\n")

    # Setup steps
    lines.append("## Setup Progress\n")
    all_done = True
    for step_key, step in status["steps"].items():
        check = "x" if step["complete"] else " "
        lines.append(f"- [{check}] **{step_key}**: {step['title']}")
        if not step["complete"]:
            all_done = False
    if all_done:
        lines.append("\nAll steps complete.")
    lines.append("")

    # KB stats
    lines.append("## Knowledge Base\n")
    lines.append(f"Total entries: {len(entries)}")
    if entries:
        by_domain: dict[str, int] = {}
        for e in entries:
            by_domain[e.domain] = by_domain.get(e.domain, 0) + 1
        for domain, count in sorted(by_domain.items()):
            lines.append(f"  - {domain}: {count}")
    lines.append("")

    # Proposals
    proposals_dir = PROJECT_ROOT / "governance" / "proposals"
    proposal_count = 0
    if proposals_dir.exists():
        proposal_count = len(list(proposals_dir.glob("*.yaml")))
    lines.append(f"## Proposals\n\nTotal: {proposal_count}\n")

    # Audit log
    lines.append("## Audit Log\n")
    lines.append(f"Total entries: {len(audit_entries)}")
    if audit_entries:
        last = audit_entries[-1]
        lines.append(f"Last entry: {last.timestamp} ({last.type})")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Resource Templates (4)
# ---------------------------------------------------------------------------


@mcp.resource("politos://kb/{domain}")
def resource_kb_by_domain(domain: str) -> str:
    """All knowledge base entries in a specific policy domain."""
    from src.core.kb import load_all_entries

    entries = [e for e in load_all_entries() if e.domain == domain]

    if not entries:
        return f"# Knowledge Base: {domain}\n\nNo entries found for domain '{domain}'."

    lines = [f"# Knowledge Base: {domain}\n"]
    lines.append(f"Total entries: {len(entries)}\n")

    for e in entries:
        lines.append(f"## {e.title} (`{e.id}`)\n")
        lines.append(f"- Version: {e.version}")
        if e.approved_by:
            lines.append(f"- Approved by: {e.approved_by}")
        if e.approved_date:
            lines.append(f"- Date: {e.approved_date}")
        lines.append(f"\n{e.content}\n")
        lines.append("---\n")

    return "\n".join(lines)


@mcp.resource("politos://kb/entry/{entry_id}")
def resource_kb_entry(entry_id: str) -> str:
    """A single knowledge base entry by its ID."""
    from src.core.kb import get_entry_by_id

    entry = get_entry_by_id(entry_id)
    if not entry:
        return f"Entry '{entry_id}' not found."

    lines = [f"# {entry.title}\n"]
    lines.append(f"- **ID**: {entry.id}")
    lines.append(f"- **Domain**: {entry.domain}")
    lines.append(f"- **Version**: {entry.version}")
    if entry.approved_by:
        lines.append(f"- **Approved by**: {entry.approved_by}")
    if entry.approved_date:
        lines.append(f"- **Date**: {entry.approved_date}")
    lines.append(f"\n{entry.content}")

    return "\n".join(lines)


@mcp.resource("politos://constitution/{section}")
def resource_constitution_section(section: str) -> str:
    """A specific section of the constitution: 'principles', 'boundaries', or 'constraints'."""
    from src.core.constitution import load_constitution

    const = load_constitution()

    section_map = {
        "principles": ("Core Principles", const.principles),
        "boundaries": ("Ethical Boundaries", const.boundaries),
        "constraints": ("Legal Constraints", const.constraints),
    }

    if section not in section_map:
        return f"Unknown section '{section}'. Use: principles, boundaries, or constraints."

    title, data = section_map[section]
    lines = [f"# {title}\n"]

    for name, rule in data.items():
        immutable = rule.get("immutable", True)
        marker = "immutable" if immutable else "mutable"

        if section == "principles":
            lines.append(f"- **{name}** [{marker}]: {rule.get('statement', '')}")
        elif section == "boundaries":
            severity = rule.get("severity", "high")
            lines.append(f"- **{name}** [{marker}, severity: {severity}]: {rule.get('description', '')}")
        elif section == "constraints":
            applies = rule.get("applies_to", [])
            suffix = f" (applies to: {', '.join(applies)})" if applies else ""
            lines.append(f"- **{name}** [{marker}]: {rule.get('description', '')}{suffix}")

    return "\n".join(lines)


@mcp.resource("politos://governance/proposal/{proposal_id}")
def resource_proposal(proposal_id: str) -> str:
    """A governance proposal by its ID."""
    proposal_path = PROJECT_ROOT / "governance" / "proposals" / f"{proposal_id}.yaml"
    if not proposal_path.exists():
        return f"Proposal '{proposal_id}' not found."

    data = yaml.safe_load(proposal_path.read_text())
    if not isinstance(data, dict):
        return f"Invalid proposal data for '{proposal_id}'."

    lines = [f"# Proposal: {data.get('title', proposal_id)}\n"]
    lines.append(f"- **ID**: {data.get('id', proposal_id)}")
    lines.append(f"- **Status**: {data.get('status', 'unknown')}")
    if data.get("affected_domains"):
        lines.append(f"- **Domains**: {', '.join(data['affected_domains'])}")
    lines.append(f"\n## Description\n\n{data.get('description', 'N/A')}")
    lines.append(f"\n## Rationale\n\n{data.get('rationale', 'N/A')}")
    if data.get("compliance"):
        lines.append(f"\n## Compliance Result\n\n{data['compliance']}")
    if data.get("counter_arguments"):
        lines.append(f"\n## Counter-Arguments\n\n{data['counter_arguments']}")
    if data.get("summary"):
        lines.append(f"\n## Summary\n\n{data['summary']}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Prompts (4)
# ---------------------------------------------------------------------------


@mcp.prompt()
def citizen_question(topic: str) -> list[dict]:
    """Ask the organization about a policy topic as a citizen.

    Searches the knowledge base, generates a cited response, and handles
    the case where no position exists yet.

    Args:
        topic: The policy topic or question to ask about.
    """
    return [
        {
            "role": "user",
            "content": f"""\
I'd like to ask about: {topic}

Instructions for the assistant:
1. First, call `politos_search_knowledge` with this topic to find relevant KB entries.
2. If entries are found, call `politos_chat` with the original question to get a \
grounded, cited response from the representative agent.
3. Present the response to me with clear source citations ([KB:id], [GOV:id], [CONST:name]).
4. If no relevant entries are found, inform me that this topic has not been decided \
yet and offer to help me draft a governance proposal using `politos_submit_proposal`.\
""",
        }
    ]


@mcp.prompt()
def submit_proposal(
    title: str,
    description: str,
    rationale: str,
    affected_domains: str,
) -> list[dict]:
    """Submit a governance proposal for deliberation.

    Pre-validates against the constitution, then submits with compliance
    check, counter-arguments, and citizen-facing summary.

    Args:
        title: Proposal title.
        description: What the proposal does.
        rationale: Why this proposal is needed.
        affected_domains: Comma-separated policy domains (e.g. "economy, environment").
    """
    domains_list = [d.strip() for d in affected_domains.split(",")]
    return [
        {
            "role": "user",
            "content": f"""\
I'd like to submit this governance proposal:

- **Title**: {title}
- **Description**: {description}
- **Rationale**: {rationale}
- **Affected domains**: {', '.join(domains_list)}

Instructions for the assistant:
1. First, call `politos_validate` with the description to pre-check constitutional \
compliance before submitting.
2. If validation passes, call `politos_submit_proposal` with title="{title}", \
description="{description}", rationale="{rationale}", \
affected_domains={domains_list}.
3. Present the results: proposal ID, compliance assessment, counter-arguments, \
and the citizen-facing summary.
4. If pre-validation fails, show me the violations and suggest revisions that \
would comply with the constitution.\
""",
        }
    ]


@mcp.prompt()
def explore_positions(domain: str | None = None) -> list[dict]:
    """Explore the organization's policy positions.

    If a domain is specified, shows all entries in that domain.
    Otherwise, shows an overview of all domains and their coverage.

    Args:
        domain: Optional policy domain to focus on (e.g. "economy", "environment").
    """
    if domain:
        return [
            {
                "role": "user",
                "content": f"""\
Show me the organization's positions on {domain}.

Instructions for the assistant:
1. Read the resource `politos://kb/{domain}` to get all entries in this domain.
2. Present each position with its title, ID, and a brief summary of the content.
3. If the domain has no entries, say so and list available domains by calling \
`politos_list_topics` and reading `politos://context/status`.\
""",
            }
        ]
    else:
        return [
            {
                "role": "user",
                "content": """\
Show me an overview of all the organization's policy positions.

Instructions for the assistant:
1. Call `politos_list_topics` to get all topic titles.
2. Read `politos://context/status` to see entry counts by domain.
3. Present the results grouped by domain: domain name, number of entries, and \
the list of topic titles in each domain.
4. Highlight any domains from `politos://context/domains` that have no entries yet.\
""",
            }
        ]


@mcp.prompt()
def founding_wizard() -> list[dict]:
    """Start or resume the founding process for a new organization.

    Guides through all 6 setup steps: identity, constitution, representative
    persona, knowledge base seeding, compliance validation, and founding report.
    """
    return [
        {
            "role": "user",
            "content": """\
I'd like to set up a new PolitOS organization (or continue an incomplete setup).

Instructions for the assistant:
1. Call `politos_setup_status` to check which steps are complete.
2. Read `politos://context/domains` to understand available policy domains.
3. Walk through each incomplete step in order:

   **Step 1 — Identity**: Ask me for organization name, short name, language, \
jurisdiction, and voting preferences. Then call `politos_setup_identity`.

   **Step 2 — Constitution**: Call `politos_setup_constitution` with no arguments \
to show current rules. Ask if I want to add custom principles, boundaries, or \
constraints. Call again with any additions.

   **Step 3 — Representative**: Ask me for the AI spokesperson's name, tone, and \
communication style. Call `politos_setup_persona`.

   **Step 4 — Knowledge Base**: Ask which approach I prefer:
   a) Import an existing document (paste text or file path)
   b) Answer guided questions per domain
   c) Both — import first, then fill gaps
   d) Skip — build positions through governance later
   For each position, call `politos_setup_seed_kb`. Show me each entry for approval.

   **Step 5+6 — Validation & Report**: Call `politos_setup_complete`. If violations \
are found, show them and help me fix or discard entries, then call again.

4. Confirm with me before each step's action. Show results after each step.
5. After completion, show the founding summary and announce the organization is ready.\
""",
        }
    ]


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


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
    from dotenv import load_dotenv

    from src.core.kb import index_knowledge_base, load_all_entries

    # Load .env from CWD (the organization's project directory)
    load_dotenv()

    # Only index if there are KB entries (avoid unnecessary ChromaDB init during clean setup)
    if load_all_entries():
        index_knowledge_base()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
