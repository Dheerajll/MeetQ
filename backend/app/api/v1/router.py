# Aggregates all v1 routers
# Imports and includes auth, users, meetings, reports, rag, lma routers
"""
Aggregates all v1 API routers.
"""
"""
Aggregates all v1 API routers.
"""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.meetings import router as meetings_router
from app.api.v1.rag import router as rag_router 

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(meetings_router)
api_router.include_router(rag_router)