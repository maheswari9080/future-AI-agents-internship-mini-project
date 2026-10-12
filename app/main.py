from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routers import students, ai

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade Student Record Management System with full CRUD, search/filter, and local AI assistant.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Jinja2 Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Include Routers
app.include_router(students.router)
app.include_router(ai.router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_dashboard(request: Request):
    """Serve the single-page admin dashboard."""
    ctx = {
        "request": request,
        "app_name": settings.APP_NAME,
    }
    try:
        return templates.TemplateResponse(request=request, name="index.html", context=ctx)
    except TypeError:
        return templates.TemplateResponse("index.html", ctx)


@app.get("/health", tags=["Health"])
def health_check():
    """System health check endpoint."""
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}
