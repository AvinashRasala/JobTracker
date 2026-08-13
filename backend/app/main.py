from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.routes import auth, applications, dashboard, gmail, documents, ai
from app.api.routes import interviews as interviews_module

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Automatically track every job application across every platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_origin_regex=settings.ALLOWED_ORIGIN_REGEX or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uploaded profile pictures live here and are served directly. check_dir=False
# so the app can still start before any avatar has ever been uploaded.
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR), check_dir=False), name="static")

app.include_router(auth.router)
app.include_router(applications.router)
app.include_router(dashboard.router)
app.include_router(interviews_module.router)
app.include_router(interviews_module.upcoming_router)
app.include_router(gmail.router)
app.include_router(documents.router)
app.include_router(ai.router)


@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
