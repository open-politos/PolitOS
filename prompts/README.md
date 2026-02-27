# Prompts

Governed prompt configurations per policy domain. These are the system prompts and instructions given to the policy engine agent.

Every prompt in this directory is subject to governance — changes require a deliberation and vote.

## Structure

```yaml
domain: "economy"
version: 2
system_prompt: |
  You are the policy engine for economic topics.
  Base your responses only on the approved knowledge base entries.
  ...
approved_by: "GOV-2026-055"
```

## Why prompts are governed

The prompts given to an AI fundamentally shape its behavior. In PolitOS, prompt changes are treated with the same seriousness as policy changes — because they effectively are policy changes.
