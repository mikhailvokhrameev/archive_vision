# /api/v1/api.py
from fastapi import APIRouter
from .endpoints import documents, reports

api_router = APIRouter()
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
