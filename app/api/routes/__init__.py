from app.api.routes.health import router as health_router
from app.api.routes.imagery import router as imagery_router
from app.api.routes.queries import router as queries_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.results import router as results_router
from app.api.routes.chat import router as chat_router
from app.api.routes.conversations import router as conversations_router
from app.api.routes.ai_status import router as ai_status_router
from app.api.routes.dataset import router as dataset_router

__all__ = [
    "health_router",
    "imagery_router",
    "queries_router",
    "analysis_router",
    "jobs_router",
    "results_router",
    "chat_router",
    "conversations_router",
    "ai_status_router",
    "dataset_router",
]
