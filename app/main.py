from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger
from app.models.database import init_db
from app.api.routes import (
    health_router,
    imagery_router,
    queries_router,
    analysis_router,
    jobs_router,
    results_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and shutdown handler."""
    logger.info("Initializing OrbitMind backend services (Env: %s, AI_MODE: %s)", settings.APP_ENV, settings.AI_MODE)
    settings.ensure_directories()
    await init_db()
    yield
    logger.info("Shutting down OrbitMind backend services.")


app = FastAPI(
    title="OrbitMind Remote Sensing AI Backend",
    description="""
# OrbitMind API
An AI-powered remote-sensing backend that allows users and systems to query satellite imagery using natural language.

### Core Capabilities:
- **Visual Question Answering (VQA)**
- **Satellite Scene Captioning**
- **Bitemporal Change Detection** (Urban expansion, deforestation, flooding)
- **Land Cover Semantic Segmentation**
- **Multimodal Optical + SAR Radar Fusion**
- **Evidence-First Georeferenced Outputs** (GeoTIFF change/segmentation masks & spatial statistics)
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health_router)
app.include_router(imagery_router)
app.include_router(queries_router)
app.include_router(analysis_router)
app.include_router(jobs_router)
app.include_router(results_router)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.warning("Validation error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "BadRequest", "detail": str(exc)}
    )


@app.exception_handler(FileNotFoundError)
async def not_found_handler(request: Request, exc: FileNotFoundError):
    logger.warning("File not found error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "NotFound", "detail": str(exc)}
    )
