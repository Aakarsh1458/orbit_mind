import json
from typing import Any, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger
from app.llm.base import BaseLLMProvider, LLMConfigurationError, LLMExecutionError

T = TypeVar("T", bound=BaseModel)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API client using REST endpoint."""

    def __init__(self):
        super().__init__(name="gemini")
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1024
    ) -> str:
        if not self.is_configured():
            raise LLMConfigurationError(self.name, "GEMINI_API_KEY is not set.")

        contents = []
        system_instruction = None

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            else:
                gemini_role = "user" if role == "user" else "model"
                contents.append({"role": gemini_role, "parts": [{"text": content}]})

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key.strip()}"

        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise LLMExecutionError(self.name, "No response candidates returned by Gemini.")
                part = candidates[0].get("content", {}).get("parts", [{}])[0]
                return part.get("text", "").strip()
        except httpx.HTTPStatusError as e:
            logger.error("Gemini API error status: %s", e.response.status_code)
            raise LLMExecutionError(self.name, f"HTTP error {e.response.status_code}") from e
        except Exception as e:
            logger.error("Gemini request failed: %s", str(e))
            raise LLMExecutionError(self.name, "Network or timeout failure") from e

    async def structured_output(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        temperature: float = 0.0
    ) -> T:
        schema = response_model.model_json_schema()
        system_prompt = (
            f"You are a strict JSON generator. Return ONLY valid JSON matching this schema:\n"
            f"{json.dumps(schema, indent=2)}\n"
            f"Do not write markdown backticks or explanations."
        )

        augmented = [{"role": "system", "content": system_prompt}] + messages
        raw_text = await self.chat(augmented, temperature=temperature)
        cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            parsed = json.loads(cleaned)
            return response_model.model_validate(parsed)
        except Exception as err:
            logger.warning("Failed to parse structured JSON from Gemini: %s", err)
            retry_augmented = augmented + [
                {"role": "model", "content": raw_text},
                {"role": "user", "content": "Your response was invalid JSON. Return ONLY raw valid JSON adhering strictly to schema."}
            ]
            retry_raw = await self.chat(retry_augmented, temperature=0.0)
            cleaned_retry = retry_raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            parsed_retry = json.loads(cleaned_retry)
            return response_model.model_validate(parsed_retry)

    async def health_check(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "provider": self.name,
                "configured": False,
                "reachable": False,
                "detail": "GEMINI_API_KEY is not configured in environment."
            }
        try:
            url = f"{self.base_url}/models/{self.model}?key={self.api_key.strip()}"
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.get(url)
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
                "detail": "Failed to reach Gemini endpoint."
            }
