from fastapi import APIRouter

from app.api.routes import (
    batch_experiments,
    datasets,
    experiments,
    items,
    login,
    uq_benchmarks,
    users,
    utils,
    websocket,
)

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(
    experiments.router, prefix="/experiments", tags=["experiments"]
)
api_router.include_router(
    batch_experiments.router, prefix="/batch-experiments", tags=["batch-experiments"]
)
api_router.include_router(
    uq_benchmarks.router, prefix="/uq-benchmarks", tags=["uq-benchmarks"]
)
api_router.include_router(websocket.router, tags=["websocket"])
