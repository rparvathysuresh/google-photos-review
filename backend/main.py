"""
FastAPI application entry point.

AI-Powered Photo Retrieval Discovery Engine — Backend API.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings, setup_logging
from backend.db.database import init_db
from backend.routers import ingest

# ── Configure Logging ─────────────────────────────────────────
setup_logging(debug=settings.DEBUG)
logger = logging.getLogger(__name__)


# ── Lifespan Event Handler ────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting Discovery Engine API...")
    init_db()
    logger.info("Database initialized")
    logger.info(f"Groq model: {settings.GROQ_MODEL}")
    logger.info(f"Embedding model: {settings.EMBEDDING_MODEL}")
    logger.info("Discovery Engine API is ready")
    yield
    # Shutdown
    logger.info("Shutting down Discovery Engine API...")


# ── FastAPI App ───────────────────────────────────────────────
app = FastAPI(
    title="Discovery Engine API",
    description=(
        "AI-Powered Photo Retrieval Discovery Engine — "
        "Ingests user feedback, extracts structured retrieval episodes, "
        "and provides RAG-based research Q&A with citations."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ── CORS Middleware ───────────────────────────────────────────
origins = [
    origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",") if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from backend.routers import ingest, rag, ask, clusters, analytics

# ── Routers ───────────────────────────────────────────────────
app.include_router(ingest.router)
app.include_router(rag.router)
app.include_router(ask.router)
app.include_router(clusters.router)
app.include_router(analytics.router)


# ── Health Check ──────────────────────────────────────────────
@app.get("/api/health", tags=["System"])
async def health_check():
    """
    Health check endpoint.

    Returns the current status of the API and its dependencies.
    """
    from backend.db.vector_store import vector_store
    
    return {
        "status": "healthy",
        "service": "discovery-engine",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "database": "connected",
            "chroma": vector_store.get_health(),
            "groq_model": settings.GROQ_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL,
        },
    }


# ── Root Redirect ─────────────────────────────────────────────
@app.get("/", tags=["System"])
async def root():
    """Redirect to API docs."""
    return {
        "message": "Discovery Engine API",
        "docs": "/docs",
        "health": "/api/health",
    }
