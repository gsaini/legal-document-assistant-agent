"""Legal Document Assistant - Main Application Entry Point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import router as api_router
from src.config import get_settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    logger.info(
        "Starting Legal Document Assistant",
        app_name=settings.app_name,
        environment=settings.app_env,
        llm_provider=settings.llm_provider,
    )
    
    # Ensure directories exist
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize vector store, embeddings, etc.
    # await initialize_vector_store()
    # await load_clause_library()
    
    yield
    
    # Cleanup
    logger.info("Shutting down Legal Document Assistant")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Legal Document Assistant",
        description=(
            "A high-precision, agentic RAG system for contract review, legal research, "
            "and automated citation mapping. Features multi-agent orchestration with "
            "Intake, Analysis, Research, Compliance, and Redlining agents.\n\n"
            "**Open Source Stack:**\n"
            "- LLM: Ollama (Llama 4, Mistral) - local, privacy-preserving\n"
            "- Vector Store: ChromaDB - open source\n"
            "- OCR: Tesseract - open source\n"
            "- NLP: spaCy + Presidio - open source"
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "app": settings.app_name,
            "environment": settings.app_env,
            "llm_provider": settings.llm_provider,
            "llm_model": (
                settings.ollama_model if settings.llm_provider == "ollama"
                else settings.openai_model if settings.llm_provider == "openai"
                else settings.anthropic_model
            ),
        }

    @app.get("/")
    async def root() -> dict:
        """Root endpoint with API information."""
        return {
            "name": "Legal Document Assistant API",
            "version": "0.1.0",
            "description": "Agentic RAG system for legal document processing",
            "docs": "/docs" if settings.debug else "Disabled in production",
            "health": "/health",
            "api_base": "/api/v1",
            "endpoints": {
                "documents": "/api/v1/documents",
                "analysis": "/api/v1/analysis",
                "research": "/api/v1/research",
                "compliance": "/api/v1/compliance",
            },
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
