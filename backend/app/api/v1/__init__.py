"""
API v1 routes.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, memories, processing, embeddings, discovery

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(memories.router)
api_router.include_router(processing.router)
api_router.include_router(embeddings.router)
api_router.include_router(discovery.router)
