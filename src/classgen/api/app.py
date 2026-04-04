"""FastAPI application factory for ClassGen.

Creates the app, mounts static files, sets up Jinja2 templates,
includes all API routers, and defines the root/health endpoints.
"""

from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

load_dotenv()

# ---------------------------------------------------------------------------
# Path resolution — use APP_ROOT env var (set in Docker) or infer from
# __file__ for local dev (3 parents up from src/classgen/api/).
# ---------------------------------------------------------------------------

_APP_ROOT = Path(os.environ.get("APP_ROOT", str(Path(__file__).resolve().parents[3])))

_templates_dir = str(_APP_ROOT / "templates")
_static_dir = str(_APP_ROOT / "static")

# Ensure static dir exists
os.makedirs(_static_dir, exist_ok=True)


# ---------------------------------------------------------------------------
# Jinja2 templates -- shared by profile and school routers
# ---------------------------------------------------------------------------

templates = Jinja2Templates(directory=_templates_dir)


# ---------------------------------------------------------------------------
# Lifespan (PDF cleanup on startup)
# ---------------------------------------------------------------------------


def _cleanup_old_pdfs(max_age_hours: int = 24):
    """Delete generated PDFs older than max_age_hours on startup."""
    cutoff = time.time() - (max_age_hours * 3600)
    count = 0
    for f in os.listdir(_static_dir):
        if f.startswith("lesson_plan_") and f.endswith(".pdf"):
            path = os.path.join(_static_dir, f)
            if os.path.getmtime(path) < cutoff:
                os.remove(path)
                count += 1
    if count:
        print(f"Cleaned up {count} old PDF(s)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _cleanup_old_pdfs()
    yield


# ---------------------------------------------------------------------------
# App creation
# ---------------------------------------------------------------------------

app = FastAPI(title="ClassGen MAP Backend", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")


# ---------------------------------------------------------------------------
# Core routes (root + health)
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = _APP_ROOT / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse(
        "<h1>ClassGen Local Backend Proxy is running.</h1><p>index.html not found.</p>"
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Include routers
# ---------------------------------------------------------------------------

from classgen.api import (  # noqa: E402
    chat,
    dev,
    homework,
    profile,
    push,
    school,
    teacher,
    webhook,
)

# Inject shared templates into routers that render Jinja2 pages
profile.templates = templates
school.templates = templates

app.include_router(chat.router)
app.include_router(webhook.router)
app.include_router(homework.router)
app.include_router(teacher.router)
app.include_router(profile.router)
app.include_router(school.router)
app.include_router(push.router)
app.include_router(dev.router)
