import json
from typing import Any, AsyncIterator, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.logging import logger
from app.llm.base import (
    BaseLLMClient,
    LLMConfigurationError,
    LLMExecutionError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
    LLMTimeoutError,
    LLMSchemaValidationError,
)

T = TypeVar("T", bound=BaseModel)


class GeminiClient(BaseLLMClient):
    """
    Production-grade Google Gemini client using asynchronous REST API with SSE streaming.
    Integrates directly with Google AI Studio (Gemini 1.5 Flash, Gemini 1.5 Pro, Gemini 2.0 Flash).
    """

    def __init__(self, default_model: Optional[str] = None):
        super().__init__(name="gemini")
        self.default_model = default_model or settings.GEMINI_MODEL
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    @property
    def api_key(self) -> Optional[str]:
        return settings.GEMINI_API_KEY

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def _format_gemini_payload(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 1024,
        response_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Converts standard OpenAI-style messages to Google Gemini API payload."""
        contents = []
        system_parts = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_parts.append({"text": content if isinstance(content, str) else str(content)})
            else:
                gemini_role = "user" if role == "user" else "model"
                parts = []
                if isinstance(content, str):
                    parts.append({"text": content})
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, str):
                            parts.append({"text": item})
                        elif isinstance(item, dict):
                            if item.get("type") == "text":
                                parts.append({"text": item.get("text", "")})
                            elif item.get("type") == "image_url":
                                # Handle inline base64 image data for multimodal VQA
                                url = item.get("image_url", {}).get("url", "")
                                if url.startswith("data:image/"):
                                    header, b64_data = url.split(";base64,", 1)
                                    mime_type = header.replace("data:", "")
                                    parts.append({
                                        "inlineData": {
                                            "mimeType": mime_type,
                                            "data": b64_data
                                        }
                                    })
                contents.append({"role": gemini_role, "parts": parts})

        gen_config: Dict[str, Any] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
        if response_schema:
            gen_config["responseMimeType"] = "application/json"
            gen_config["responseSchema"] = response_schema

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": gen_config,
        }
        if system_parts:
            payload["systemInstruction"] = {"parts": system_parts}

        return payload

    def _handle_http_error(self, err: httpx.HTTPStatusError) -> None:
        """Translates HTTP status codes into typed LLM exceptions."""
        status = err.response.status_code
        try:
            body = err.response.json()
            msg = body.get("error", {}).get("message", err.response.text)
        except Exception:
            msg = err.response.text

        logger.warning("Gemini HTTP error (%d): %s", status, msg)
        if status == 429:
            raise LLMRateLimitError(self.name, f"Gemini quota/rate limit exceeded: {msg}") from err
        elif status == 503:
            raise LLMServiceUnavailableError(self.name, f"Gemini service unavailable: {msg}") from err
        elif status in (408, 504):
            raise LLMTimeoutError(self.name, f"Gemini gateway timeout ({status}): {msg}") from err
        else:
            raise LLMExecutionError(self.name, f"Gemini HTTP {status}: {msg}", status_code=status) from err

    async def generate_chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> str:
        if not self.is_configured():
            raise LLMConfigurationError(self.name, "GEMINI_API_KEY is not configured.")

        target_model = model or self.default_model
        payload = self._format_gemini_payload(messages, temperature=temperature, max_tokens=max_tokens)
        url = f"{self.base_url}/models/{target_model}:generateContent?key={self.api_key.strip()}"

        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise LLMExecutionError(self.name, "No response candidates returned by Gemini.")
                part = candidates[0].get("content", {}).get("parts", [{}])[0]
                text = part.get("text", "").strip()
                return text
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except httpx.TimeoutException as e:
            logger.error("Gemini request timed out after %ds", settings.REQUEST_TIMEOUT_SECONDS)
            raise LLMTimeoutError(self.name, "Gemini request timed out.") from e
        except Exception as e:
            logger.error("Gemini generate_chat error: %s", str(e))
            raise LLMExecutionError(self.name, f"Network or execution failure: {str(e)}") from e

    async def generate_structured(
        self,
        messages: List[Dict[str, Any]],
        response_model: Type[T],
        model: Optional[str] = None,
        temperature: float = 0.0,
    ) -> T:
        schema = response_model.model_json_schema()
        system_instruction = (
            f"You are an expert remote sensing JSON schema parser. "
            f"You MUST return strictly valid JSON matching this schema:\n"
            f"{json.dumps(schema, indent=2)}\n"
            f"Do not write markdown backticks or reasoning preamble."
        )

        augmented_messages = [{"role": "system", "content": system_instruction}] + messages
        raw_text = await self.generate_chat(
            messages=augmented_messages,
            model=model,
            temperature=temperature,
            max_tokens=2048,
        )

        cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        if "{" in cleaned and "}" in cleaned:
            s_idx = cleaned.find("{")
            e_idx = cleaned.rfind("}") + 1
            cleaned = cleaned[s_idx:e_idx]

        try:
            parsed = json.loads(cleaned)
            return response_model.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError) as parse_err:
            logger.warning("Gemini structured output parsing failed: %s. Attempting repair retry...", parse_err)
            repair_messages = augmented_messages + [
                {"role": "model", "content": raw_text},
                {"role": "user", "content": f"Your response was invalid. Error: {str(parse_err)}. Return ONLY raw valid JSON adhering strictly to schema."}
            ]
            try:
                repair_raw = await self.generate_chat(
                    messages=repair_messages,
                    model=model,
                    temperature=0.0,
                    max_tokens=2048,
                )
                cleaned_repair = repair_raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                if "{" in cleaned_repair and "}" in cleaned_repair:
                    s_idx = cleaned_repair.find("{")
                    e_idx = cleaned_repair.rfind("}") + 1
                    cleaned_repair = cleaned_repair[s_idx:e_idx]
                parsed_repair = json.loads(cleaned_repair)
                return response_model.model_validate(parsed_repair)
            except Exception as repair_err:
                raise LLMSchemaValidationError(
                    self.name,
                    f"Gemini failed schema validation after repair attempt: {str(repair_err)}"
                ) from repair_err

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        if not self.is_configured():
            raise LLMConfigurationError(self.name, "GEMINI_API_KEY is not configured.")

        target_model = model or self.default_model
        payload = self._format_gemini_payload(messages, temperature=temperature, max_tokens=max_tokens)
        url = f"{self.base_url}/models/{target_model}:streamGenerateContent?alt=sse&key={self.api_key.strip()}"

        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        await response.aread()
                        response.raise_for_status()

                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line.removeprefix("data:").strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(data_str)
                            candidates = chunk_data.get("candidates", [])
                            if candidates:
                                part = candidates[0].get("content", {}).get("parts", [{}])[0]
                                text_chunk = part.get("text", "")
                                if text_chunk:
                                    yield text_chunk
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(self.name, "Gemini streaming request timed out.") from e
        except Exception as e:
            raise LLMExecutionError(self.name, f"Gemini streaming error: {str(e)}") from e

    async def health_check(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "provider": self.name,
                "configured": False,
                "reachable": False,
                "detail": "GEMINI_API_KEY is not configured in environment.",
            }
        try:
            url = f"{self.base_url}/models/{self.default_model}?key={self.api_key.strip()}"
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.get(url)
                reachable = res.status_code == 200
                return {
                    "provider": self.name,
                    "configured": True,
                    "reachable": reachable,
                    "model": self.default_model,
                }
        except Exception as e:
            return {
                "provider": self.name,
                "configured": True,
                "reachable": False,
                "detail": f"Failed to reach Gemini endpoint: {str(e)}",
            }


# Backwards-compatibility alias
GeminiProvider = GeminiClient
