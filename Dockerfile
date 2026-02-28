FROM python:3.12-slim AS base

WORKDIR /app

# Install dependencies first (cached layer)
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy project files
COPY . .

# --- FastAPI target (default) ---
FROM base AS api
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# --- MCP server target (stdio) ---
FROM base AS mcp
CMD ["python", "-m", "src.mcp_server"]
