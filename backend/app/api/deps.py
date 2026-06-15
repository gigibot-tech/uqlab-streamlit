from collections.abc import Generator
from typing import Annotated
import logging

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.models import TokenPayload
from app.tables import User
from app.services.metrics_service import MetricsService
from app.services.storage.base import MetricsStorage
from app.services.storage.postgres import PostgresStorage
from app.services.storage.wxgov import WxGovStorage

logger = logging.getLogger(__name__)

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


def get_metrics_service(session: SessionDep) -> MetricsService:
    """Create and configure MetricsService with enabled storage backends.
    
    This function implements dependency injection for the metrics service,
    instantiating storage backends based on configuration settings.
    
    Returns:
        MetricsService instance with configured storage backends
    """
    storages: list[MetricsStorage] = []
    
    # Add PostgreSQL storage if enabled
    if settings.ENABLE_POSTGRES:
        try:
            postgres_storage = PostgresStorage(session)
            storages.append(postgres_storage)
            logger.info("Enabled PostgreSQL storage backend")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL storage: {str(e)}")
    
    # Add wx.gov storage if enabled and configured
    if settings.ENABLE_WXGOV:
        if not all([settings.WXGOV_API_KEY, settings.WXGOV_SPACE_ID, settings.WXGOV_URL]):
            logger.warning(
                "wx.gov storage enabled but not fully configured. "
                "Required: WXGOV_API_KEY, WXGOV_SPACE_ID, WXGOV_URL"
            )
        else:
            try:
                # Type assertion: we've checked all values are not None above
                wxgov_storage = WxGovStorage(
                    api_key=str(settings.WXGOV_API_KEY),
                    space_id=str(settings.WXGOV_SPACE_ID),
                    url=str(settings.WXGOV_URL)
                )
                storages.append(wxgov_storage)
                logger.info("Enabled watsonx.governance storage backend")
            except Exception as e:
                logger.error(f"Failed to initialize wx.gov storage: {str(e)}")
    
    if not storages:
        logger.warning("No storage backends enabled! Metrics will not be persisted.")
    
    return MetricsService(storages)


MetricsServiceDep = Annotated[MetricsService, Depends(get_metrics_service)]
