import logging
from contextlib import asynccontextmanager
from pathlib import Path

# Bootstrap ``src/`` before any route imports ``uqlab`` / ``uqlab_orchestrator``.
from app.core.ml_bootstrap import SRC_DIR, ensure_ml_paths, verify_ml_stack

ensure_ml_paths()
verify_ml_stack()

from fastapi import FastAPI
from fastapi.routing import APIRoute
from sqlmodel import Session
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.db import engine, init_db
from app.storage.factory import get_storage_backend

logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_ml_paths()
    verify_ml_stack()
    logger.info("ML stack: uqlab from %s", SRC_DIR)
    storage_backend = get_storage_backend()
    logger.info("✅ Active storage backend ready: %s", storage_backend.name)
    
    # Initialize database (create tables for SQLite)
    with Session(engine) as session:
        init_db(session)
    
    logger.info("✅ Database initialized successfully")
    logger.info(f"✅ Server startup complete - ready to accept requests")
    
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    swagger_ui_parameters={"persistAuthorization": True},
    lifespan=lifespan,
)


# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.include_router(api_router, prefix=settings.API_V1_STR)
