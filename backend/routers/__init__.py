"""Backend API routers package."""
from .dashboard import router as dashboard_router
from .reports import router as reports_router
from .upload import router as upload_router

__all__ = ["dashboard_router", "reports_router", "upload_router"]

