# PolitOS — Roadmap

## Phase 1: Specification (current)

- [x] Core repository structure
- [x] Constitution layer (core principles, ethical boundaries, legal constraints)
- [x] Governance rules (voting, deliberation, sortition)
- [x] Membership model (tiers, rights matrix)
- [x] Agent definitions (representative, policy-engine, advocate, compliance, summarizer, kb-curator, moderator)
- [x] Audit log format
- [x] Example party configuration
- [x] CLAUDE.md as dev/test runtime
- [ ] Proposal lifecycle spec (`governance/proposal-lifecycle.yaml`)
- [ ] Constitutional amendment process (`governance/constitutional-amendment.yaml`)
- [ ] Onboarding flow spec (`membership/onboarding.yaml`)
- [ ] Prompt governance spec (how prompt changes go through deliberation)
- [ ] Knowledge base entry format spec
- [ ] Agent interaction model (how agents communicate with each other)

## Phase 2: Core Platform

### Tech Stack
- **Language:** Python
- **Agent Orchestration:** CrewAI
- **LLM Abstraction:** LiteLLM (Claude, OpenAI, Ollama, Mistral — one interface)
- **Knowledge Base:** Markdown/YAML in Git (source of truth) + ChromaDB (vector search)
- **API:** FastAPI
- **Web Frontend:** Next.js (later, separate repo `politos-web`)

### Architecture

```
┌─────────────────────────────────┐
│         politos-web             │  Next.js
│     (Website + Member Portal)   │
└────────────────┬────────────────┘
                 │ REST/GraphQL
┌────────────────▼────────────────┐
│         PolitOS Core API        │  FastAPI
└────────────────┬────────────────┘
                 │
┌────────────────▼────────────────┐
│         Agent Layer             │  CrewAI
│  policy-engine · representative │
│  advocate · compliance · ...    │
└────────────────┬────────────────┘
                 │
┌────────────────▼────────────────┐
│         LiteLLM Adapter         │  LiteLLM
│  Claude · OpenAI · Ollama · ... │
└─────────────────────────────────┘
                 │
┌────────────────▼────────────────┐
│      Knowledge Base + Git       │  Markdown + ChromaDB
└─────────────────────────────────┘
```

### Repo Structure

```
politos/
├── CLAUDE.md                     # Dev/test runtime (Claude Code)
├── constitution/                 # Hardcoded ethical & legal constraints
├── governance/                   # Voting rules, deliberation protocols, sortition
├── agents/                       # Agent specs (YAML) — read by CrewAI
├── knowledge-base/               # Markdown + YAML — source for ChromaDB
├── membership/                   # Membership tiers, rights matrix
├── audit-log/                    # Append-only governance log
├── config/                       # Party configuration templates
├── src/                          # Python backend
│   ├── agents/                   # CrewAI agent implementations
│   │   ├── representative.py    # Loads agents/representative/*.yaml
│   │   ├── compliance.py        # Validates against constitution/
│   │   ├── advocate.py          # Generates counter-arguments
│   │   ├── policy_engine.py     # Generates policy from KB
│   │   ├── summarizer.py        # Citizen-facing summaries
│   │   ├── kb_curator.py        # Proposes KB updates
│   │   └── moderator.py         # Manages deliberation lifecycle
│   ├── core/
│   │   ├── llm.py               # LiteLLM configuration
│   │   ├── kb.py                # ChromaDB integration, loads knowledge-base/
│   │   └── audit.py             # Audit log service
│   ├── api/                     # FastAPI endpoints
│   │   ├── chat.py              # Citizen interaction with representative
│   │   ├── proposals.py         # Submit/review proposals
│   │   └── governance.py        # Governance status, audit log queries
│   └── main.py                  # FastAPI app entrypoint
├── pyproject.toml
└── docs/
```

### Implementation Tasks

- [ ] Project setup (pyproject.toml, dependencies: crewai, litellm, chromadb, fastapi, pyyaml)
- [ ] LiteLLM adapter (`src/core/llm.py`) — reads LLM config from party.config.yaml
- [ ] ChromaDB integration (`src/core/kb.py`) — indexes knowledge-base/ into vector store
- [ ] Audit log service (`src/core/audit.py`) — append-only YAML writer
- [ ] Compliance agent (`src/agents/compliance.py`) — loads constitution, validates inputs
- [ ] Representative agent (`src/agents/representative.py`) — loads persona/boundaries, uses KB
- [ ] Advocate agent (`src/agents/advocate.py`) — generates counter-arguments
- [ ] Policy engine agent (`src/agents/policy_engine.py`) — generates policy from KB
- [ ] CrewAI orchestration — wire agents together for proposal workflow
- [ ] FastAPI endpoints — chat, proposals, governance queries
- [ ] Proposal lifecycle — file-based state machine in governance/proposals/

## Phase 3: Sub-Projects

### politos-web
Party website + member portal. Next.js frontend that talks to the Core API.
- Repo: `open-politos/politos-web`
- Static generation from knowledge base for public site
- Dynamic member portal for proposals, deliberation, voting

### politos-identity
Branding & visual identity generator. Logo, colors, typography based on party config.
- Repo: `open-politos/politos-identity`

### politos-templates
Preconfigured starter packages for different organizational types.
- Repo: `open-politos/politos-templates`

## Phase 4: Production Readiness

- [ ] Authentication & membership service
- [ ] Identity verification (privacy-preserving)
- [ ] Voting infrastructure (cryptographic, verifiable)
- [ ] Deployment guides (Docker, cloud)
- [ ] Multi-language support
- [ ] Audit log integrity (hash chain or IPFS)

## Open Questions

- How is identity verification handled without compromising privacy?
- Should the audit log use a blockchain-like hash chain, or is git history sufficient?
- How does the system handle multiple languages?
- What is the minimum viable governance process for the first real-world pilot?
- CrewAI vs LangGraph — which fits PolitOS agent interactions better?
- How do organizations update PolitOS (OS) independently from their own data?
