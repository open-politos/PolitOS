# Policy Engine Agent

The core agent that generates policy positions based on the approved knowledge base and governed prompts.

## Responsibilities

- Generate policy responses grounded in the knowledge base
- Refuse to answer on topics without governance decisions
- Cite sources for every claim
- Flag potential conflicts between positions

## Inputs

- Knowledge base entries (`knowledge-base/`)
- Governed prompts (`prompts/`)
- Constitution constraints (`constitution/`)

## Outputs

- Policy position drafts (for governance approval)
- Responses to policy queries (from representative agent)
- Conflict reports (to compliance agent)
