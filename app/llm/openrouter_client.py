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


class OpenRouterClient(BaseLLMClient):
    """
    OpenRouter Gateway Client using OpenAI-compatible SDK semantics.
    Enables access to Claude 3.5 Sonnet, GPT-4o, DeepSeek-R1/Chat, and Llama 3.3 70B
    via https://openrouter.ai/api/v1.
    """

    def __init__(self, name: str = "openrouter", default_model: Optional[str] = None):
        super().__init__(name=name)
        self.default_model = default_model
        self.base_url = "https://openrouter.ai/api/v1"
        self._openai_client = None

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

    def _get_openai_client(self):
        """Lazily initializes the AsyncOpenAI client with OpenRouter base URL."""
        if self._openai_client is None:
            try:
                from openai import AsyncOpenAI
                key = self.api_key or "dummy_unconfigured"
                self._openai_client = AsyncOpenAI(
                    base_url=self.base_url,
                    api_key=key.strip(),
                    default_headers={
                        "HTTP-Referer": "http://localhost:8000",
                        "X-Title": "OrbitMind",
                    },
                    timeout=settings.REQUEST_TIMEOUT_SECONDS,
                )
            except ImportError:
                self._openai_client = None
        return self._openai_client

    def _translate_error(self, err: Exception) -> Exception:
        """Translates OpenAI or HTTPX status codes to domain-specific LLM exceptions."""
        err_str = str(err)
        status_code = getattr(err, "status_code", None)
        
        # Check HTTP status code if present
        if status_code == 429 or "429" in err_str or "rate limit" in err_str.lower():
            return LLMRateLimitError(self.name, f"Rate limit reached on OpenRouter: {err_str}")
        elif status_code == 503 or "503" in err_str or "overloaded" in err_str.lower():
            return LLMServiceUnavailableError(self.name, f"OpenRouter model unavailable/overloaded: {err_str}")
        elif status_code in (408, 504) or "timeout" in err_str.lower():
            return LLMTimeoutError(self.name, f"OpenRouter request timed out: {err_str}")
        
        return LLMExecutionError(self.name, err_str, status_code=status_code)

    async def generate_chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> str:
        if not self.is_configured():
            raise LLMConfigurationError(self.name, f"{self.name.upper()}_API_KEY or OPENROUTER_API_KEY is not set.")

        target_model = model or self.model
        client = self._get_openai_client()

        if client:
            try:
                response = await client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max(max_tokens, 256),
                )
                choice = response.choices[0].message
                content = choice.content or ""
                # Some reasoning models return reasoning content when content is blank
                if not content.strip() and getattr(choice, "reasoning", None):
                    content = choice.reasoning
                return content.strip()
            except Exception as e:
                logger.error("OpenRouter AsyncOpenAI client error: %s", str(e))
                raise self._translate_error(e) from e

        # Fallback to direct HTTPX if openai client could not be imported
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "OrbitMind",
            "Content-Type": "application/json"
        }
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max(max_tokens, 256)
        }

        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as http_client:
                res = await http_client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                choice = data["choices"][0]["message"]
                content = choice.get("content") or ""
                if not content.strip() and choice.get("reasoning"):
                    content = choice.get("reasoning")
                return content.strip()
        except httpx.HTTPStatusError as e:
            raise self._translate_error(e) from e
        except Exception as e:
            raise self._translate_error(e) from e

    async def generate_structured(
        self,
        messages: List[Dict[str, Any]],
        response_model: Type[T],
        model: Optional[str] = None,
        temperature: float = 0.0,
    ) -> T:
        schema = response_model.model_json_schema()
        system_instruction = (
            f"You are a strict JSON schema generator for geospatial intelligence. "
            f"You must respond ONLY with valid JSON matching this schema:\n"
            f"{json.dumps(schema, indent=2)}\n"
            f"Do not include markdown code blocks, backticks, or reasoning preamble. "
            f"Return ONLY the raw JSON object starting with {{ and ending with }}."
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
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}") + 1
            cleaned = cleaned[start_idx:end_idx]

        try:
            parsed = json.loads(cleaned)
            return response_model.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError) as parse_err:
            logger.warning("Failed to parse structured output from %s: %s. Attempting repair...", self.name, parse_err)
            repair_messages = augmented_messages + [
                {"role": "assistant", "content": raw_text},
                {"role": "user", "content": f"Your response was invalid JSON. Error: {str(parse_err)}. Output ONLY raw JSON matching schema."}
            ]
            try:
                retry_raw = await self.generate_chat(
                    messages=repair_messages,
                    model=model,
                    temperature=0.0,
                    max_tokens=2048,
                )
                cleaned_retry = retry_raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                if "{" in cleaned_retry and "}" in cleaned_retry:
                    s_idx = cleaned_retry.find("{")
                    e_idx = cleaned_retry.rfind("}") + 1
                    cleaned_retry = cleaned_retry[s_idx:e_idx]
                parsed_retry = json.loads(cleaned_retry)
                return response_model.model_validate(parsed_retry)
            except Exception as repair_err:
                raise LLMSchemaValidationError(
                    self.name,
                    f"OpenRouter structured parsing failed after retry: {str(repair_err)}"
                ) from repair_err

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        if not self.is_configured():
            raise LLMConfigurationError(self.name, f"{self.name.upper()}_API_KEY or OPENROUTER_API_KEY is not set.")

        target_model = model or self.model
        client = self._get_openai_client()

        if client:
            try:
                stream = await client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max(max_tokens, 256),
                    stream=True,
                )
                async for chunk in stream:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        text = getattr(delta, "content", "") or ""
                        if text:
                            yield text
                return
            except Exception as e:
                logger.error("OpenRouter streaming error: %s", str(e))
                raise self._translate_error(e) from e

        # HTTPX streaming fallback
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "OrbitMind",
            "Content-Type": "application/json"
        }
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max(max_tokens, 256),
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as http_client:
                async with http_client.stream("POST", f"{self.base_url}/chat/completions", headers=headers, json=payload) as res:
                    if res.status_code != 200:
                        await res.aread()
                        res.raise_for_status()
                    async for line in res.aiter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line.removeprefix("data:").strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(data_str)
                            delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            raise self._translate_error(e) from e

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
        except Exception as e:
            return {
                "provider": self.name,
                "configured": True,
                "reachable": False,
                "detail": f"Failed to reach {self.name} endpoint: {str(e)}"
            }


# Backwards-compatibility alias
OpenRouterProvider = OpenRouterClient
