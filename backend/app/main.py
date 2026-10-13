from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.database.database import Base, engine
from app.models import models  # noqa: F401 (ensures models are registered on Base)
from app.routers import auth, catalog, complaints, dashboard, notifications, users

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Smart Campus Complaint & Issue Tracking System (CampusResolve) API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables automatically for local/dev use. In production, prefer Alembic
# migrations (see backend/alembic) so schema changes are tracked and reviewable.
Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(catalog.router)
app.include_router(complaints.router)
app.include_router(notifications.router)
app.include_router(dashboard.router)

try:
    import os

    os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIRECTORY), name="uploads")
except Exception:
    pass


@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": settings.APP_NAME}
