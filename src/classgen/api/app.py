"""FastAPI application factory for ClassGen.

Creates the app, mounts static files, sets up Jinja2 templates,
includes all API routers, and defines the root/health endpoints.
"""

from __future__ import annotations

import hashlib
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.gzip import GZipMiddleware
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
_assets_dir = str(_APP_ROOT / "assets")

# Ensure static + assets dirs exist
os.makedirs(_static_dir, exist_ok=True)
os.makedirs(_assets_dir, exist_ok=True)


# ---------------------------------------------------------------------------
# Jinja2 templates -- shared by profile, school, and root routes
# ---------------------------------------------------------------------------

templates = Jinja2Templates(directory=_templates_dir)


# ---------------------------------------------------------------------------
# Asset hashing -- compute once at startup. Browsers can cache /assets/* for
# a year (immutable) because the URL changes whenever the file content does.
# ---------------------------------------------------------------------------


def _compute_asset_urls() -> dict[str, str]:
    urls: dict[str, str] = {}
    for key, name in [("css_url", "app.css"), ("js_url", "app.js")]:
        path = Path(_assets_dir) / name
        if path.exists():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()[:8]
            stem, _, ext = name.partition(".")
            urls[key] = f"/assets/{stem}.{digest}.{ext}"
        else:
            urls[key] = f"/assets/{name}"
    return urls


_asset_urls = _compute_asset_urls()


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
# Gzip text responses >1KB. Idempotent under Caddy/nginx-proxy: they pass through
# already-encoded responses, so this is defense-in-depth for raw uvicorn dev runs.
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.middleware("http")
async def cache_headers(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/assets/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif path in ("/", "/terms"):
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    return response


# ---------------------------------------------------------------------------
# Core routes (root + health)
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html", {**_asset_urls})


@app.get("/assets/app.{hash_part}.{ext}")
async def hashed_asset(hash_part: str, ext: str):
    expected = _asset_urls.get(f"{ext}_url", "")
    if not expected.endswith(f".{hash_part}.{ext}"):
        raise HTTPException(status_code=404)
    name = {"css": "app.css", "js": "app.js"}.get(ext)
    if not name:
        raise HTTPException(status_code=404)
    media = "text/css" if ext == "css" else "application/javascript"
    return FileResponse(str(Path(_assets_dir) / name), media_type=media)


@app.get("/terms", response_class=HTMLResponse)
async def terms_page():
    terms_path = _APP_ROOT / "terms.html"
    if terms_path.exists():
        return FileResponse(str(terms_path))
    return HTMLResponse(
        "<h1>Terms & Privacy</h1><p>Page not available.</p>",
        status_code=500,
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
