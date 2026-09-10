from fastapi import APIRouter
from app.core.config import settings
from app.schemas.response import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Service health check endpoint.
    Confirms that the OrbitMind API server is alive and operational.
    """
    return HealthResponse(
        status="ok",
        service="orbitmind-backend",
        version=settings.APP_VERSION,
        ai_mode=settings.AI_MODE
    )
