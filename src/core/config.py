"""Loads party.config.yaml and exposes a typed Config object."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


DEFAULTS: dict[str, Any] = {
    "version": "0.1.0",
    "organization": {
        "name": "PolitOS Organization",
        "short_name": "PolitOS",
        "language": "en",
        "jurisdiction": None,
        "founded": None,
        "website": None,
    },
    "llm": {
        "provider": "claude",
        "model": "claude-opus-4-6",
        "fallback": None,
        "temperature": 0.3,
        "max_tokens": 4096,
    },
    "representative": {
        "name": "Party Spokesperson",
        "language": "en",
        "tone": "clear, respectful, factual",
    },
    "membership": {
        "open_registration": True,
        "approval_required": False,
        "tiers": [],
    },
    "governance": {
        "voting_method": "approval",
        "standard_quorum": 0.1,
        "standard_threshold": 0.6,
    },
    "audit": {
        "storage": "local",
        "public_access": True,
        "retention_days": None,
    },
}


@dataclass
class LLMConfig:
    provider: str = "claude"
    model: str = "claude-opus-4-6"
    fallback: str | None = None
    temperature: float = 0.3
    max_tokens: int = 4096


@dataclass
class OrganizationConfig:
    name: str = "PolitOS Organization"
    short_name: str = "PolitOS"
    language: str = "en"
    jurisdiction: str | None = None
    founded: str | None = None
    website: str | None = None


@dataclass
class RepresentativeConfig:
    name: str = "Party Spokesperson"
    language: str = "en"
    tone: str = "clear, respectful, factual"


@dataclass
class AuditConfig:
    storage: str = "local"
    public_access: bool = True
    retention_days: int | None = None


@dataclass
class Config:
    version: str = "0.1.0"
    organization: OrganizationConfig = field(default_factory=OrganizationConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    representative: RepresentativeConfig = field(default_factory=RepresentativeConfig)
    audit: AuditConfig = field(default_factory=AuditConfig)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge override into base recursively."""
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(root: Path | None = None) -> Config:
    """Load party config from YAML, merged with defaults."""
    root = root or PROJECT_ROOT
    config_path = root / "config" / "party.config.yaml"
    if not config_path.exists():
        config_path = root / "config" / "party.config.example.yaml"

    raw: dict[str, Any] = {}
    if config_path.exists():
        raw = yaml.safe_load(config_path.read_text()) or {}

    merged = _deep_merge(DEFAULTS, raw)

    org = merged.get("organization", {})
    llm = merged.get("llm", {})
    rep = merged.get("representative", {})
    audit = merged.get("audit", {})

    return Config(
        version=merged.get("version", "0.1.0"),
        organization=OrganizationConfig(**org),
        llm=LLMConfig(**llm),
        representative=RepresentativeConfig(**rep),
        audit=AuditConfig(**audit),
        raw=merged,
    )
