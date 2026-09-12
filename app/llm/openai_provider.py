import json
from typing import Any, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger
from app.llm.base import BaseLLMProvider, LLMConfigurationError, LLMExecutionError

T = TypeVar("T", bound=BaseModel)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API client implementation using HTTPX."""

    def __init__(self):
        super().__init__(name="openai")
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.base_url = "https://api.openai.com/v1"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1024
    ) -> str:
        if not self.is_configured():
            raise LLMConfigurationError(self.name, "OPENAI_API_KEY is not set.")

        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
                res = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"].strip()
        except httpx.HTTPStatusError as e:
            logger.error("OpenAI API error status: %s", e.response.status_code)
            raise LLMExecutionError(self.name, f"HTTP error {e.response.status_code}") from e
        except Exception as e:
            logger.error("OpenAI request failed: %s", str(e))
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
            f"Do not include markdown code blocks, backticks, or preamble."
        )

        augmented_messages = [{"role": "system", "content": system_prompt}] + messages
        raw_text = await self.chat(augmented_messages, temperature=temperature)
        cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            parsed = json.loads(cleaned)
            return response_model.model_validate(parsed)
        except Exception as err:
            logger.warning("Failed to parse structured output from OpenAI: %s", err)
            # Second attempt with stricter prompt
            retry_messages = augmented_messages + [
                {"role": "assistant", "content": raw_text},
                {"role": "user", "content": "Your response was invalid JSON. Return ONLY the raw JSON object conforming exactly to the schema."}
            ]
            retry_raw = await self.chat(retry_messages, temperature=0.0)
            cleaned_retry = retry_raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            parsed_retry = json.loads(cleaned_retry)
            return response_model.model_validate(parsed_retry)

    async def health_check(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "provider": self.name,
                "configured": False,
                "reachable": False,
                "detail": "OPENAI_API_KEY is not configured in environment."
            }
        try:
            # Low cost models check
            headers = {"Authorization": f"Bearer {self.api_key.strip()}"}
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.get(f"{self.base_url}/models", headers=headers)
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
                "detail": "Failed to reach OpenAI endpoint."
            }
