from api.v1.routers import (
    auth_router,
    healthcheck_router,
    permission_router,
    roles_router,
    users_router,
)
from fastapi import FastAPI


def register_routers(app: FastAPI) -> bool:
    app.include_router(auth_router)
    app.include_router(healthcheck_router)
    app.include_router(roles_router)
    app.include_router(permission_router)
    app.include_router(users_router)

    return True
