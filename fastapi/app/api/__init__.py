from fastapi import APIRouter

from app.api import (
    agent,
    auth,
    care,
    community,
    elders,
    files,
    knowledge,
    logs,
    medications,
    menus,
    notifications,
    profile,
    roles,
    services,
    users,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(menus.router)
api_router.include_router(roles.router)
api_router.include_router(profile.router)
api_router.include_router(files.router)
api_router.include_router(logs.router)
api_router.include_router(elders.router)
api_router.include_router(medications.router)
api_router.include_router(services.router)
api_router.include_router(care.router)
api_router.include_router(agent.router)
api_router.include_router(community.router)
api_router.include_router(knowledge.router)
api_router.include_router(notifications.router)
