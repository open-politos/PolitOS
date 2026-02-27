# LLM Adapters — Base Interface

Abstract interface for LLM backend integration. PolitOS is model-agnostic.

## Supported Providers

| Provider | Status |
|---|---|
| Claude (Anthropic) | Planned |
| OpenAI | Planned |
| Ollama (local) | Planned |
| Mistral | Planned |
| Custom | Planned |

## Configuration

Set your provider in `config/party.config.yaml`:

```yaml
llm:
  provider: "claude"
  model: "claude-opus-4-6"
  fallback: "ollama/llama3"
```

## Adapter Implementations

Full adapter implementations are maintained in the separate repository:
[`open-politos/politos-adapters`](https://github.com/open-politos/politos-adapters)
