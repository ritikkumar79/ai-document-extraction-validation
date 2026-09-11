
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.routes.documents import router as documents_router
from app.core.database import init_db
from app.core.logging import configure_logging

configure_logging()
init_db()

app = FastAPI(
    title="Document Intelligence API",
    version="1.0.0",
    description="AI-powered financial document extraction, validation and persistence platform.",
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router, prefix="/api/v1")

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/dashboard")

@app.get("/docs", include_in_schema=False)
def custom_docs():
    """Swagger UI with a small navigation control back to the dashboard."""
    response = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        swagger_ui_parameters={"persistAuthorization": True},
    )
    html = response.body.decode("utf-8")
    navigation = """
    <style>
      .docintel-nav {
        position: fixed; top: 14px; left: 18px; z-index: 9999;
        display: inline-flex; align-items: center; gap: 8px;
        padding: 9px 14px; border-radius: 8px;
        background: #0b1220; color: #fff; text-decoration: none;
        font: 700 13px/1.2 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
        box-shadow: 0 6px 18px rgba(11,18,32,.18);
      }
      .docintel-nav:hover { background: #17243a; }
      .docintel-nav span { font-size: 16px; }
      @media (max-width: 700px) {
        .docintel-nav { top: 10px; left: 10px; padding: 8px 11px; font-size: 12px; }
        .swagger-ui .information-container { padding-top: 48px; }
      }
    </style>
    <a class="docintel-nav" href="/dashboard" aria-label="Back to DocIntel dashboard">
      <span>←</span> Back to Dashboard
    </a>
    """
    return HTMLResponse(html.replace("<body>", "<body>" + navigation))


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    from fastapi.responses import FileResponse
    return FileResponse(FRONTEND_DIR / "templates" / "dashboard.html")

@app.get("/result/{document_name}", include_in_schema=False)
def result_page(document_name: str):
    from fastapi.responses import FileResponse
    return FileResponse(FRONTEND_DIR / "templates" / "document_result.html")

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "document-intelligence", "version": "1.0.0"}
