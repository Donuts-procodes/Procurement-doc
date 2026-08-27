import os

target_file = r"C:\Users\DELL\work\bigzbyagent\voicelatex-agents\apps\procurement-service\src\app_factory.py"

new_content = """import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from src.middleware import log_requests, validation_exception_handler
# Import the migrated routers
from src.routers import routes_generate, routes_knowledge, routes_session, routes_sessions

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize PostgreSQL safely
    try:
        from src.db.database import Base, engine
        from src.db import models
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"⚠️ Could not initialize PostgreSQL: {e}")
    yield
    # Cleanup logic (if any) goes here

def create_app() -> FastAPI:
    # Inject lifespan into FastAPI app
    app = FastAPI(title="Procurement Service API", lifespan=lifespan)

    raw_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000")
    allowed_origins = [orig.strip() for orig in raw_origins.split(",") if orig.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(log_requests)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # Mount migrated routes
    app.include_router(routes_session.router)
    app.include_router(routes_knowledge.router)
    app.include_router(routes_generate.router)
    app.include_router(routes_sessions.router)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "procurement-generator"}
        
    return app
"""

with open(target_file, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Successfully updated app_factory.py")
