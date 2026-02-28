"""FastAPI application setup."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.audit import router as audit_router
from src.api.chat import router as chat_router
from src.api.knowledge import router as knowledge_router
from src.api.proposals import router as proposals_router
from src.core.config import load_config
from src.core.kb import index_knowledge_base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load config and index knowledge base."""
    cfg = load_config()
    app.state.config = cfg
    count = index_knowledge_base()
    print(f"PolitOS: Indexed {count} knowledge base entries")
    yield


def create_app() -> FastAPI:
    cfg = load_config()

    app = FastAPI(
        title=f"{cfg.organization.name} — PolitOS API",
        description="AI-governed political organization runtime",
        version=cfg.version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat_router, tags=["Chat"])
    app.include_router(proposals_router, tags=["Proposals"])
    app.include_router(knowledge_router, tags=["Knowledge Base"])
    app.include_router(audit_router, tags=["Audit"])

    @app.get("/")
    async def root():
        return {
            "name": cfg.organization.name,
            "version": cfg.version,
            "status": "running",
        }

    return app
