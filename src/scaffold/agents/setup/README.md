# Setup Agent (Founding Wizard)

Guides the founding of a new PolitOS organization through a multi-step interactive process.

## Responsibilities

- Initialize organization configuration (`party.config.yaml`)
- Walk founders through constitutional review and customization
- Configure the representative agent persona
- Seed the knowledge base from documents or guided questions
- Validate all content against the constitution via the compliance agent
- Generate a founding resolution and audit log entry

## Activation

The setup agent activates automatically when:
- No `config/party.config.yaml` exists and the knowledge base is empty
- A user says "setup", "found a party", or "founding mode"

## Files

- `persona.yaml` — Agent identity, voice, greeting, navigation commands
- `boundaries.yaml` — What the setup agent can and cannot do
- `steps.yaml` — The multi-step founding process definition
- `domains.yaml` — Policy domain definitions and guiding questions
- `founding-resolution-template.yaml` — Template for the founding governance record

## Process

1. **Organization Identity** — Name, language, jurisdiction, governance parameters
2. **Constitutional Review** — Review defaults, optionally add custom principles
3. **Representative Persona** — Name, tone, language style for the AI spokesperson
4. **Knowledge Base Seeding** — Import documents or answer guided questions
5. **Compliance Validation** — Every KB entry checked against the constitution
6. **Founding Report** — Summary, founding resolution, audit log entry
