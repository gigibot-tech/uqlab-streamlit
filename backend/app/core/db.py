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
        from app.tables import Item, UncertaintyExperiment  # noqa: F401
        
        # Create all tables
        SQLModel.metadata.create_all(engine)

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
