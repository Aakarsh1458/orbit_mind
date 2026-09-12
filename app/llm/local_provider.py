import json
from typing import Any, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger
from app.llm.base import BaseLLMProvider, LLMExecutionError

T = TypeVar("T", bound=BaseModel)


class LocalLLMProvider(BaseLLMProvider):
    """Local OpenAI-compatible API client (e.g. Ollama, vLLM, LocalAI)."""

    def __init__(self):
        super().__init__(name="local")
        self.base_url = settings.LOCAL_LLM_URL.rstrip("/")
        self.model = "default"

    def is_configured(self) -> bool:
        return bool(self.base_url)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1024
    ) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
                res = await client.post(f"{self.base_url}/chat/completions", json=payload)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error("Local LLM request failed at %s: %s", self.base_url, str(e))
            raise LLMExecutionError(self.name, f"Local endpoint {self.base_url} error: {e}") from e

    async def structured_output(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        temperature: float = 0.0
    ) -> T:
        schema = response_model.model_json_schema()
        system_prompt = f"Return ONLY valid JSON adhering strictly to this schema:\n{json.dumps(schema)}"
        augmented = [{"role": "system", "content": system_prompt}] + messages
        raw = await self.chat(augmented, temperature=temperature)
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(cleaned)
        return response_model.model_validate(parsed)

    async def health_check(self) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                res = await client.get(f"{self.base_url}/models")
                return {
                    "provider": self.name,
                    "configured": True,
                    "reachable": res.status_code == 200,
                    "url": self.base_url
                }
        except Exception:
            return {
                "provider": self.name,
                "configured": True,
                "reachable": False,
                "url": self.base_url
            }
