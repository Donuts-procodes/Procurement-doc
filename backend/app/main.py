from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Configure comprehensive backend stdout logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("gdocs.main")
logger.info("Initializing FastAPI Backend with verbose logging...")

from app.api.v1 import (
    routes_generate,
    routes_knowledge,
    routes_session,
    routes_sessions,
    routes_subagents,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Managed startup/shutdown lifecycle for database and external services."""
    # --- Startup ---
    logger.info("🚀 Running lifespan startup: creating database tables...")
    try:
        from app.db.database import Base, engine
        from app.db import models  # noqa: F401 — ensure models are registered
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified successfully.")
    except Exception as exc:
        logger.error(f"⚠️ Database initialization failed (non-fatal): {exc}")
        logger.warning("Server will start but database-dependent endpoints may fail until PostgreSQL is available.")

    yield

    # --- Shutdown ---
    logger.info("🛑 FastAPI shutdown complete.")


app = FastAPI(title="Docs RAG Clone API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"--> Incoming {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"<-- Completed {request.method} {request.url.path} with status {response.status_code}")
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"❌ 422 VALIDATION ERROR on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"💥 500 INTERNAL ERROR on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "message": str(exc)},
    )

app.include_router(routes_session.router, prefix="/api/v1")
app.include_router(routes_knowledge.router, prefix="/api/v1")
app.include_router(routes_generate.router, prefix="/api/v1")
app.include_router(routes_sessions.router, prefix="/api/v1")
app.include_router(routes_subagents.router, prefix="/api/v1/subagents", tags=["Subagents"])


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
