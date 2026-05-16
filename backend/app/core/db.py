from sqlmodel import Session, SQLModel, create_engine, select

from app import crud
from app.core.config import settings
from app.models import UserCreate
from app.tables import User

# Create engine with appropriate settings
engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    connect_args={"check_same_thread": False} if settings.USE_SQLITE else {},
)


# make sure all SQLModel models are imported (app.tables) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # For SQLite in-memory, we must create tables on startup
    # For PostgreSQL, use Alembic migrations
    if settings.USE_SQLITE:
        # Import all models to ensure they're registered
        from app.tables import (  # noqa: F401
            BatchExperiment,
            BatchExperimentRun,
            Item,
            UncertaintyExperiment,
        )
        
        # Create all tables
        SQLModel.metadata.create_all(engine)
        
        # Validate critical tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        required_tables = ["batchexperiment", "batchexperimentrun", "uncertaintyexperiment"]
        existing_tables = inspector.get_table_names()
        
        missing_tables = [t for t in required_tables if t not in existing_tables]
        if missing_tables:
            raise RuntimeError(
                f"❌ CRITICAL: Required database tables missing: {missing_tables}\n"
                f"   Existing tables: {existing_tables}\n"
                f"   This indicates a database initialization failure.\n"
                f"   Please delete app.db and restart the server."
            )

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)
