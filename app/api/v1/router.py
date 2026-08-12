"""API v1 router — aggregates all v1 endpoint modules."""

from fastapi import APIRouter

from app.api.v1 import findings, health, reports, scans

api_v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

api_v1_router.include_router(health.router)
api_v1_router.include_router(scans.router)
api_v1_router.include_router(reports.router)
api_v1_router.include_router(findings.router)
