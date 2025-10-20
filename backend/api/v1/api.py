# /api/v1/api.py
from fastapi import APIRouter
from api.v1.endpoints import documents, reports, corrections

api_router = APIRouter()
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(corrections.router, prefix="/documents", tags=["Corrections"])
api_router.include_router(corrections.router, prefix="/documents", tags=["Corrections"])
