"""FastAPI Application Entry Point for AI Post-Sales Feedback Intelligence."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from auth import router as auth_router, verify_access_token
from routers import dashboard_router, reports_router, upload_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup hook. The in-memory store needs no initialization — it starts empty."""
    yield


app = FastAPI(
    title="Customer Intelligence: AI Post-Sales Feedback & Failure Prediction API",
    description=(
        "Backend system for post-sales customer feedback ingestion, NLP sentiment classification, "
        "severity prioritization, symptom extraction, statistical anomaly/early-warning detection, "
        "and forward-looking failure root-cause prediction. Uses a lightweight in-memory store "
        "(no external database required)."
    ),
    version="3.0.0",
    lifespan=lifespan,
)

# Enable CORS for React frontend development and production hosting
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def require_api_login(request: Request, call_next):
    if (
        request.url.path.startswith("/api/")
        and request.url.path != "/api/auth/login"
        and request.method != "OPTIONS"
    ):
        authorization = request.headers.get("authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not verify_access_token(token):
            return JSONResponse(
                status_code=401,
                content={"detail": "Sign in to access the feedback intelligence API."},
                headers={"WWW-Authenticate": "Bearer"},
            )
    return await call_next(request)

# Register functional system routers
app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(reports_router)
app.include_router(dashboard_router)


@app.get("/", tags=["Health"])
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend operational readiness."""
    return {
        "status": "healthy",
        "service": "AI Post-Sales Feedback Intelligence Engine",
        "version": "3.0.0",
        "storage": "in-memory (no external database)",
        "endpoints": {
            "upload": "POST /api/upload",
            "dashboard_summary": "GET /api/dashboard/summary",
            "daily_trends": "GET /api/dashboard/daily-trends",
            "anomaly_alerts": "GET /api/alerts",
            "future_predictions": "GET /api/predictions",
            "historical_reports": "GET /api/reports",
            "report_detail": "GET /api/reports/{id}",
            "feedback_search": "GET /api/feedback",
            "docs": "/docs",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
