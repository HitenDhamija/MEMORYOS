"""
Main FastAPI application with enhanced security.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pathlib import Path
from app.core.config import settings
from app.middleware.cors import setup_cors
from app.middleware.request_id import RequestIDMiddleware
from app.api.v1 import api_router
from app.db.session import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

# Create upload directory
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

# Initialize app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

# Add security middleware (order matters!)
# 1. Request ID tracking first (for all logs)
app.add_middleware(RequestIDMiddleware)

# 2. CORS after request ID
setup_cors(app)

# Include routes
app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "environment": settings.environment}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
