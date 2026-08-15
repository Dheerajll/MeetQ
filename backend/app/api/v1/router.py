# Aggregates all v1 routers
# Imports and includes auth, users, meetings, reports, rag, lma routers
"""
Aggregates all v1 API routers.
"""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router

api_router = APIRouter()

# Mount the auth router
api_router.include_router(auth_router)

# Future routers will be added here:
# from app.api.v1.meetings import router as meetings_router
# api_router.include_router(meetings_router)