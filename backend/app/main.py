from contextlib import asynccontextmanager
from pathlib import Path
import logging

from fastapi import FastAPI
from fastapi.routing import APIRoute
from sqlmodel import Session
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.db import engine, init_db

logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation: Check ML script exists
    ml_script_path = Path(settings.DTAG_ROOT) / "run_fast_uncertainty_classification.py"
    if not ml_script_path.exists():
        error_msg = (
            f"❌ STARTUP FAILED: ML script not found at {ml_script_path}\n"
            f"   Expected location: {ml_script_path.absolute()}\n"
            f"   DTAG_ROOT setting: {settings.DTAG_ROOT}\n"
            f"   Please ensure the ML script is in the correct location."
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    logger.info(f"✅ ML script found at: {ml_script_path.absolute()}")
    
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
