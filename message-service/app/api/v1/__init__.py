"""API v1 Endpoints."""

from fastapi import APIRouter
from app.api.v1 import messages, llm

# Create v1 router
router = APIRouter(prefix="/api/v1")

# Include routers
router.include_router(messages.router, tags=["Messages"])
router.include_router(llm.router, tags=["LLM Processing"])