from fastapi import APIRouter
from typing import Dict, Any

from backend.services.analytics.metrics import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/dashboard")
def get_dashboard_metrics() -> Dict[str, Any]:
    """Get aggregate metrics for the dashboard."""
    return analytics_service.get_dashboard_metrics()
