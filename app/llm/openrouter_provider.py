import json
from typing import Any, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger
from app.llm.base import BaseLLMProvider, LLMConfigurationError, LLMExecutionError

T = TypeVar("T", bound=BaseModel)


class OpenRouterProvider(BaseLLMProvider):
    """
    OpenRouter / NVIDIA Nemotron API client implementation using HTTPX.
    Supports OpenRouter routing and Nemotron reasoning models.
    """

    def __init__(self, name: str = "openrouter", default_model: Optional[str] = None):
        super().__init__(name=name)
        self.default_model = default_model
        self.base_url = "https://openrouter.ai/api/v1"

    @property
    def api_key(self) -> Optional[str]:
        if self.name == "nemotron":
            return settings.NEMOTRON_API_KEY or settings.OPENROUTER_API_KEY
        return settings.OPENROUTER_API_KEY or settings.NEMOTRON_API_KEY

    @property
    def model(self) -> str:
        if self.default_model:
            return self.default_model
        if self.name == "nemotron":
            return settings.NEMOTRON_MODEL or "nvidia/nemotron-3.5-lightning:free"
        return settings.OPENROUTER_MODEL or "nvidia/nemotron-3.5-lightning:free"

    def is_configured(self) -> bool:
        key = self.api_key
        return bool(key and key.strip())

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1024
    ) -> str:
        if not self.is_configured():
            raise LLMConfigurationError(self.name, f"{self.name.upper()}_API_KEY or OPENROUTER_API_KEY is not set.")

        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "OrbitMind",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max(max_tokens, 512)
        }

        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
                res = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                choice = data["choices"][0]["message"]
                content = choice.get("content") or ""
                # Fallback to reasoning if content is empty (e.g. strict reasoning output)
                if not content.strip() and choice.get("reasoning"):
                    content = choice.get("reasoning")
                return content.strip()
        except httpx.HTTPStatusError as e:
            logger.error("%s API error status: %s", self.name, e.response.status_code)
            raise LLMExecutionError(self.name, f"HTTP error {e.response.status_code}") from e
        except Exception as e:
            logger.error("%s request failed: %s", self.name, str(e))
            raise LLMExecutionError(self.name, "Network or timeout failure") from e

    async def structured_output(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        temperature: float = 0.0
    ) -> T:
        schema = response_model.model_json_schema()
        system_prompt = (
            f"You are a strict JSON generator. You must respond ONLY with valid JSON matching this schema:\n"
            f"{json.dumps(schema, indent=2)}\n"
            f"Do not include markdown code blocks, backticks, reasoning text, or preamble. Return ONLY the raw JSON object."
        )

        augmented_messages = [{"role": "system", "content": system_prompt}] + messages
        raw_text = await self.chat(augmented_messages, temperature=temperature, max_tokens=1024)
        cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        # If model outputs preamble before first { and after last }
        if "{" in cleaned and "}" in cleaned:
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}") + 1
            cleaned = cleaned[start_idx:end_idx]

        try:
            parsed = json.loads(cleaned)
            return response_model.model_validate(parsed)
        except Exception as err:
            logger.warning("Failed to parse structured output from %s: %s", self.name, err)
            retry_messages = augmented_messages + [
                {"role": "assistant", "content": raw_text},
                {"role": "user", "content": "Your response was invalid JSON. Output ONLY the raw JSON object conforming exactly to schema, starting with { and ending with }."}
            ]
            retry_raw = await self.chat(retry_messages, temperature=0.0, max_tokens=1024)
            cleaned_retry = retry_raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            if "{" in cleaned_retry and "}" in cleaned_retry:
                s_idx = cleaned_retry.find("{")
                e_idx = cleaned_retry.rfind("}") + 1
                cleaned_retry = cleaned_retry[s_idx:e_idx]
            parsed_retry = json.loads(cleaned_retry)
            return response_model.model_validate(parsed_retry)

    async def health_check(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "provider": self.name,
                "configured": False,
                "reachable": False,
                "detail": f"{self.name.upper()}_API_KEY or OPENROUTER_API_KEY is not configured in environment."
            }
        try:
            headers = {"Authorization": f"Bearer {self.api_key.strip()}"}
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.get(f"{self.base_url}/auth/key", headers=headers)
                reachable = res.status_code == 200
                return {
                    "provider": self.name,
                    "configured": True,
                    "reachable": reachable,
                    "model": self.model
                }
        except Exception:
            return {
                "provider": self.name,
                "configured": True,
                "reachable": False,
                "detail": f"Failed to reach {self.name} endpoint."
            }
