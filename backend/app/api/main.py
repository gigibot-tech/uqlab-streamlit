from fastapi import APIRouter

from app.api.routes import datasets, experiments, items, login, users, utils

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(
    experiments.router, prefix="/experiments", tags=["experiments"]
)
