from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status

from app.ai.registry import model_registry
from app.core.config import settings
from app.llm.router import llm_router

router = APIRouter(prefix="/api/v1/ai", tags=["AI Engine & Providers"])


@router.get("/status", summary="Get overall AI system status")
async def get_ai_status() -> Dict[str, Any]:
    """
    Returns high-level status of AI inference subsystems, default LLM provider,
    compute device, and specialist model readiness.
    Never exposes API keys or credentials.
    """
    default_provider = settings.DEFAULT_LLM_PROVIDER
    provider_inst = llm_router.get_provider(default_provider)
    llm_configured = provider_inst.is_configured()

    model_tasks = ["vqa", "captioning", "change_detection", "segmentation", "optical_sar", "cloud_removal"]
    specialist_statuses = {}
    for t in model_tasks:
        try:
            m = model_registry.get_model(t, mode=settings.AI_MODE)
            specialist_statuses[t] = "available" if m.is_loaded else "ready"
        except Exception:
            specialist_statuses[t] = "unavailable"

    return {
        "ai_mode": settings.AI_MODE,
        "llm": {
            "default_provider": default_provider,
            "status": "configured" if llm_configured else "unconfigured"
        },
        "device": settings.get_effective_device(),
        "specialist_models": specialist_statuses
    }


@router.get("/models", summary="List registered specialist models and capabilities")
async def list_models() -> List[Dict[str, Any]]:
    """Returns the list of registered specialist models along with their declarative capabilities."""
    return model_registry.list_model_details()


@router.get("/providers", summary="List supported LLM orchestration providers")
async def list_providers() -> List[Dict[str, Any]]:
    """Lists supported LLM providers and configuration status."""
    return llm_router.list_providers()


@router.post("/providers/{provider}/validate", summary="Safely validate LLM provider configuration")
async def validate_provider(provider: str) -> Dict[str, Any]:
    """
    Checks whether a specific provider is configured and reachable.
    NEVER returns or logs the secret API key.
    """
    try:
        p = llm_router.get_provider(provider)
        health = await p.health_check()
        return health
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown provider '{provider}'. Available: {list(llm_router._providers.keys())}"
        )
    except Exception as e:
        return {
            "provider": provider,
            "configured": False,
            "reachable": False,
            "error": str(e)
        }
