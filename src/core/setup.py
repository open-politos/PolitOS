"""Setup wizard core logic — pure functions for the founding process.

Called by MCP tools. No conversational logic here; the MCP client's LLM
handles the multi-step conversation.
"""

import re
from datetime import date
from pathlib import Path

import yaml

from src.core.config import PROJECT_ROOT, load_config

ALLOWED_VOTING_METHODS = ["approval", "ranked-choice", "simple-majority"]


# ---------------------------------------------------------------------------
# 1. get_setup_status
# ---------------------------------------------------------------------------

def get_setup_status(root: Path | None = None) -> dict:
    """Check which founding steps are complete using state detection
    from agents/setup/steps.yaml. Returns step completion map + current
    config if it exists."""
    root = root or PROJECT_ROOT

    config_path = root / "config" / "party.config.yaml"
    persona_path = root / "agents" / "representative" / "persona.yaml"
    founding_path = root / "governance" / "decisions" / "FOUNDING-001.yaml"
    kb_dir = root / "knowledge-base"

    # Step 1: config exists
    step1 = config_path.exists()

    # Step 2: custom constitutional additions (check for immutable: false entries)
    step2 = False
    for fname in ("core-principles.yaml", "ethical-boundaries.yaml", "legal-constraints.yaml"):
        fpath = root / "constitution" / fname
        if fpath.exists():
            data = yaml.safe_load(fpath.read_text()) or {}
            section_key = {
                "core-principles.yaml": "principles",
                "ethical-boundaries.yaml": "boundaries",
                "legal-constraints.yaml": "constraints",
            }[fname]
            for _name, rule in (data.get(section_key) or {}).items():
                if isinstance(rule, dict) and rule.get("immutable") is False:
                    step2 = True
                    break
        if step2:
            break
    # Also true if step 1 done (user may have confirmed defaults are fine)
    if step1:
        step2 = True

    # Step 3: persona name differs from default
    step3 = False
    if persona_path.exists():
        persona_data = yaml.safe_load(persona_path.read_text()) or {}
        step3 = persona_data.get("name", "Party Spokesperson") != "Party Spokesperson"

    # Step 4: any YAML files in KB subdirectories
    step4 = False
    if kb_dir.exists():
        for p in kb_dir.rglob("*.yaml"):
            if p.parent != kb_dir:  # must be in a subdirectory
                step4 = True
                break

    # Step 5: FOUNDING-001 with compliance_validated: true
    step5 = False
    if founding_path.exists():
        fd = yaml.safe_load(founding_path.read_text()) or {}
        sections = fd.get("sections", {})
        kb_section = sections.get("knowledge_base", {})
        step5 = kb_section.get("compliance_validated") is True

    # Step 6: FOUNDING-001 with status: enacted
    step6 = False
    if founding_path.exists():
        fd = yaml.safe_load(founding_path.read_text()) or {}
        step6 = fd.get("status") == "enacted"

    result: dict = {
        "steps": {
            "1_identity": {"title": "Organization Identity", "complete": step1},
            "2_constitution": {"title": "Constitutional Review", "complete": step2},
            "3_representative": {"title": "Representative Persona", "complete": step3},
            "4_knowledge_base": {"title": "Knowledge Base Seeding", "complete": step4},
            "5_validation": {"title": "Compliance Validation", "complete": step5},
            "6_founding_report": {"title": "Founding Report", "complete": step6},
        },
        "all_complete": all([step1, step2, step3, step4, step5, step6]),
    }

    if step1:
        cfg = load_config(root)
        result["current_config"] = {
            "name": cfg.organization.name,
            "short_name": cfg.organization.short_name,
            "language": cfg.organization.language,
            "jurisdiction": cfg.organization.jurisdiction,
            "founded": cfg.organization.founded,
        }

    return result


# ---------------------------------------------------------------------------
# 2. get_domains
# ---------------------------------------------------------------------------

def get_domains(root: Path | None = None) -> list[dict]:
    """Load agents/setup/domains.yaml. Returns domains with guiding questions
    and a has_entries flag per domain."""
    root = root or PROJECT_ROOT
    domains_path = root / "agents" / "setup" / "domains.yaml"
    data = yaml.safe_load(domains_path.read_text()) or {}

    kb_dir = root / "knowledge-base"
    result = []
    for key, domain in (data.get("domains") or {}).items():
        subdir = domain.get("subdirectory") or key
        has_entries = False
        domain_dir = kb_dir / subdir
        if domain_dir.exists():
            has_entries = any(domain_dir.glob("*.yaml"))

        result.append({
            "key": key,
            "display_name": domain.get("display_name", key),
            "description": domain.get("description", ""),
            "subdirectory": subdir,
            "guiding_questions": domain.get("guiding_questions", []),
            "has_entries": has_entries,
        })

    return result


# ---------------------------------------------------------------------------
# 3. write_identity
# ---------------------------------------------------------------------------

def write_identity(fields: dict, root: Path | None = None) -> dict:
    """Load party.config.example.yaml as template, override with user fields,
    validate bounds, set founded to today, write party.config.yaml."""
    root = root or PROJECT_ROOT
    template_path = root / "config" / "party.config.example.yaml"
    output_path = root / "config" / "party.config.yaml"

    template = yaml.safe_load(template_path.read_text()) or {}

    # Apply user fields
    org = template.setdefault("organization", {})
    for key in ("name", "short_name", "language", "jurisdiction", "website"):
        if key in fields:
            org[key] = fields[key]

    # Set founded date to today
    org["founded"] = str(date.today())

    # Governance fields
    gov = template.setdefault("governance", {})
    if "voting_method" in fields:
        vm = fields["voting_method"]
        if vm not in ALLOWED_VOTING_METHODS:
            return {"error": f"voting_method must be one of {ALLOWED_VOTING_METHODS}, got '{vm}'"}
        gov["voting_method"] = vm

    if "standard_quorum" in fields:
        sq = float(fields["standard_quorum"])
        if sq < 0.05 or sq > 1.0:
            return {"error": f"standard_quorum must be between 0.05 and 1.0, got {sq}"}
        gov["standard_quorum"] = sq

    if "standard_threshold" in fields:
        st = float(fields["standard_threshold"])
        if st < 0.5 or st > 1.0:
            return {"error": f"standard_threshold must be between 0.5 and 1.0, got {st}"}
        gov["standard_threshold"] = st

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.dump(
        template, default_flow_style=False, allow_unicode=True, sort_keys=False,
    ))

    return {"written": str(output_path.relative_to(root)), "config": template}


# ---------------------------------------------------------------------------
# 4. add_constitutional_rules
# ---------------------------------------------------------------------------

def add_constitutional_rules(
    principles: list[dict] | None = None,
    boundaries: list[dict] | None = None,
    constraints: list[dict] | None = None,
    root: Path | None = None,
) -> dict:
    """Append custom rules to constitution files with immutable: false.
    Reject name collisions with existing keys.
    If all args are None/empty, return current constitution read-only."""
    root = root or PROJECT_ROOT
    constitution_dir = root / "constitution"

    files_map = {
        "principles": ("core-principles.yaml", "principles"),
        "boundaries": ("ethical-boundaries.yaml", "boundaries"),
        "constraints": ("legal-constraints.yaml", "constraints"),
    }

    # Load current state
    current: dict = {}
    for section, (fname, section_key) in files_map.items():
        fpath = constitution_dir / fname
        raw_text = fpath.read_text()
        data = yaml.safe_load(raw_text) or {}
        current[section] = data.get(section_key, {})

    inputs = {
        "principles": principles,
        "boundaries": boundaries,
        "constraints": constraints,
    }

    # If nothing to add, return read-only view
    if not any(inputs.values()):
        return {"mode": "read_only", "constitution": current}

    added: dict = {"principles": [], "boundaries": [], "constraints": []}
    errors: list[str] = []

    for section, items in inputs.items():
        if not items:
            continue
        fname, section_key = files_map[section]
        fpath = constitution_dir / fname

        # Read the raw text to preserve header comments
        raw_text = fpath.read_text()
        data = yaml.safe_load(raw_text) or {}
        existing = data.setdefault(section_key, {})

        for item in items:
            name = item.get("name")
            if not name:
                errors.append(f"Missing 'name' in {section} item: {item}")
                continue
            if name in existing:
                errors.append(f"Name collision in {section}: '{name}' already exists")
                continue

            # Build the rule entry
            if section == "principles":
                existing[name] = {
                    "statement": item.get("statement", ""),
                    "immutable": False,
                }
            elif section == "boundaries":
                existing[name] = {
                    "description": item.get("description", ""),
                    "severity": item.get("severity", "high"),
                    "immutable": False,
                }
            elif section == "constraints":
                existing[name] = {
                    "description": item.get("description", ""),
                    "applies_to": item.get("applies_to", []),
                    "immutable": False,
                }
            added[section].append(name)

        # Preserve header comments by re-writing just the YAML portion
        # Find where YAML content starts (after header comments)
        lines = raw_text.split("\n")
        header_lines = []
        for line in lines:
            if line.startswith("#") or line.strip() == "":
                header_lines.append(line)
            else:
                break

        header = "\n".join(header_lines) + "\n" if header_lines else ""
        yaml_content = yaml.dump(
            data, default_flow_style=False, allow_unicode=True, sort_keys=False,
        )
        fpath.write_text(header + yaml_content)

    result: dict = {"added": added}
    if errors:
        result["errors"] = errors
    return result


# ---------------------------------------------------------------------------
# 5. write_persona
# ---------------------------------------------------------------------------

def write_persona(fields: dict, root: Path | None = None) -> dict:
    """Read existing persona.yaml to preserve structure, update fields,
    write persona file. Also update party.config.yaml if it exists."""
    root = root or PROJECT_ROOT
    persona_path = root / "agents" / "representative" / "persona.yaml"

    # Load existing persona
    persona = yaml.safe_load(persona_path.read_text()) or {}

    # Update fields
    if "name" in fields:
        persona["name"] = fields["name"]
    voice = persona.setdefault("voice", {})
    if "tone" in fields:
        voice["tone"] = fields["tone"]
    if "language_level" in fields:
        voice["language_level"] = fields["language_level"]
    if "formality" in fields:
        voice["formality"] = fields["formality"]
    if "fallback_response" in fields:
        persona["fallback_response"] = fields["fallback_response"]

    # Write persona file (preserve header comment)
    raw_text = persona_path.read_text()
    lines = raw_text.split("\n")
    header_lines = []
    for line in lines:
        if line.startswith("#") or line.strip() == "":
            header_lines.append(line)
        else:
            break
    header = "\n".join(header_lines) + "\n" if header_lines else ""
    yaml_content = yaml.dump(
        persona, default_flow_style=False, allow_unicode=True, sort_keys=False,
    )
    persona_path.write_text(header + yaml_content)

    # Also update party.config.yaml if it exists
    config_path = root / "config" / "party.config.yaml"
    if config_path.exists():
        config = yaml.safe_load(config_path.read_text()) or {}
        rep = config.setdefault("representative", {})
        if "name" in fields:
            rep["name"] = fields["name"]
        if "tone" in fields:
            rep["tone"] = fields["tone"]
        config_path.write_text(yaml.dump(
            config, default_flow_style=False, allow_unicode=True, sort_keys=False,
        ))

    return {"written": str(persona_path.relative_to(root)), "persona": persona}


# ---------------------------------------------------------------------------
# 6. write_kb_entry
# ---------------------------------------------------------------------------

def write_kb_entry(
    domain: str,
    title: str,
    content: str,
    entry_id: str | None = None,
    topic_hint: str | None = None,
    root: Path | None = None,
) -> dict:
    """Write a knowledge base entry. Auto-generates ID by scanning existing
    entries. Validates domain (no path traversal). Creates subdirectory."""
    root = root or PROJECT_ROOT
    kb_dir = root / "knowledge-base"

    # Validate domain — no path traversal
    if ".." in domain or "/" in domain or "\\" in domain:
        return {"error": f"Invalid domain name: '{domain}'"}

    # Auto-generate entry ID
    if not entry_id:
        from src.core.kb import load_all_entries

        existing = load_all_entries(root)
        year = str(date.today().year)
        max_num = 0
        pattern = re.compile(rf"^kb-{year}-(\d{{3}})$")
        for e in existing:
            m = pattern.match(e.id)
            if m:
                max_num = max(max_num, int(m.group(1)))
        entry_id = f"kb-{year}-{max_num + 1:03d}"

    # Derive topic_hint from title if not given
    if not topic_hint:
        topic_hint = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        if not topic_hint:
            topic_hint = "entry"

    # Create domain subdirectory
    domain_dir = kb_dir / domain
    domain_dir.mkdir(parents=True, exist_ok=True)

    # Get founding date from config if available
    config_path = root / "config" / "party.config.yaml"
    approved_date = str(date.today())
    if config_path.exists():
        cfg = yaml.safe_load(config_path.read_text()) or {}
        org = cfg.get("organization", {})
        if org.get("founded"):
            approved_date = str(org["founded"])

    entry_data = {
        "id": entry_id,
        "domain": domain,
        "title": title,
        "content": content,
        "approved_by": "FOUNDING-001",
        "approved_date": approved_date,
        "version": 1,
        "supersedes": None,
    }

    file_path = domain_dir / f"{topic_hint}.yaml"
    file_path.write_text(yaml.dump(
        entry_data, default_flow_style=False, allow_unicode=True, sort_keys=False,
    ))

    return {
        "entry": entry_data,
        "file_path": str(file_path.relative_to(root)),
    }


# ---------------------------------------------------------------------------
# 7. validate_all_kb_entries
# ---------------------------------------------------------------------------

def validate_all_kb_entries(root: Path | None = None) -> dict:
    """Load all KB entries and validate each against the constitution.
    Returns {total, valid, violations, all_valid}."""
    root = root or PROJECT_ROOT
    from src.core.kb import load_all_entries
    from src.core.constitution import load_constitution, validate

    entries = load_all_entries(root)
    if not entries:
        return {"total": 0, "valid": 0, "violations": [], "all_valid": True}

    constitution = load_constitution(root)
    violations: list[dict] = []
    valid_count = 0

    for entry in entries:
        result = validate(entry.content, constitution)
        if result.valid:
            valid_count += 1
        else:
            violations.append({
                "entry_id": entry.id,
                "entry_title": entry.title,
                "violations": [
                    {"source": v.source, "description": v.description}
                    for v in result.violations
                ],
            })

    return {
        "total": len(entries),
        "valid": valid_count,
        "violations": violations,
        "all_valid": len(violations) == 0,
    }


# ---------------------------------------------------------------------------
# 8. create_founding_report
# ---------------------------------------------------------------------------

def create_founding_report(root: Path | None = None) -> dict:
    """Load template, fill with actual values, write FOUNDING-001.yaml,
    log founding event, return summary."""
    root = root or PROJECT_ROOT

    from src.core.kb import load_all_entries
    from src.core.audit import log as audit_log

    # Load template
    template_path = root / "agents" / "setup" / "founding-resolution-template.yaml"
    template_data = yaml.safe_load(template_path.read_text()) or {}
    report = dict(template_data.get("template", {}))

    # Load config
    cfg = load_config(root)
    org_name = cfg.organization.name
    founded = cfg.organization.founded or str(date.today())
    rep_name = cfg.representative.name

    # Fill placeholders
    report["title"] = f"Founding Resolution of {org_name}"
    report["date"] = founded
    report["description"] = (
        f"This resolution records the founding of {org_name} and establishes "
        "its initial configuration, constitutional framework, and knowledge base entries. "
        "All initial knowledge base entries are approved under this resolution as the "
        "founding positions of the organization. These positions may be amended through "
        "the standard governance process.\n"
    )
    report["enacted_date"] = founded

    # Populate sections
    sections = report.setdefault("sections", {})

    # Representative
    rep_section = sections.setdefault("representative", {})
    rep_section["name"] = rep_name

    # KB entries
    entries = load_all_entries(root)
    entry_ids = [e.id for e in entries]
    domains_covered = sorted(set(e.domain for e in entries))

    kb_section = sections.setdefault("knowledge_base", {})
    kb_section["entries"] = entry_ids
    kb_section["domains_covered"] = domains_covered
    kb_section["compliance_validated"] = True

    # Custom constitutional additions
    const_section = sections.setdefault("constitution", {})
    custom_additions: list[str] = []
    for fname, section_key in [
        ("core-principles.yaml", "principles"),
        ("ethical-boundaries.yaml", "boundaries"),
        ("legal-constraints.yaml", "constraints"),
    ]:
        fpath = root / "constitution" / fname
        if fpath.exists():
            data = yaml.safe_load(fpath.read_text()) or {}
            for name, rule in (data.get(section_key) or {}).items():
                if isinstance(rule, dict) and rule.get("immutable") is False:
                    custom_additions.append(f"{section_key}:{name}")
    const_section["custom_additions"] = custom_additions

    # Write founding resolution
    decisions_dir = root / "governance" / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    report_path = decisions_dir / "FOUNDING-001.yaml"
    report_path.write_text(yaml.dump(
        report, default_flow_style=False, allow_unicode=True, sort_keys=False,
    ))

    # Audit log
    audit_log(
        type="founding_event",
        topic=f"Organization founding: {org_name}",
        sources=["GOV:FOUNDING-001"],
        root=root,
    )

    # Build summary
    # Count constitutional principles
    const_dir = root / "constitution"
    principle_count = 0
    for fname, section_key in [
        ("core-principles.yaml", "principles"),
        ("ethical-boundaries.yaml", "boundaries"),
        ("legal-constraints.yaml", "constraints"),
    ]:
        fpath = const_dir / fname
        if fpath.exists():
            data = yaml.safe_load(fpath.read_text()) or {}
            principle_count += len(data.get(section_key) or {})

    # Count entries by domain
    entries_by_domain: dict[str, int] = {}
    for e in entries:
        entries_by_domain[e.domain] = entries_by_domain.get(e.domain, 0) + 1

    return {
        "founding_resolution": "FOUNDING-001",
        "organization": org_name,
        "language": cfg.organization.language,
        "jurisdiction": cfg.organization.jurisdiction,
        "founded": founded,
        "constitutional_rules": principle_count,
        "custom_additions": len(custom_additions),
        "representative_name": rep_name,
        "representative_tone": cfg.representative.tone,
        "kb_entries_total": len(entries),
        "kb_entries_by_domain": entries_by_domain,
        "domains_covered": domains_covered,
        "report_file": str(report_path.relative_to(root)),
    }
