import json
from typing import Any, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger
from app.llm.base import BaseLLMProvider, LLMConfigurationError, LLMExecutionError

T = TypeVar("T", bound=BaseModel)


class HuggingFaceProvider(BaseLLMProvider):
    """Hugging Face Inference API client."""

    def __init__(self):
        super().__init__(name="huggingface")
        self.token = settings.HF_TOKEN
        self.model_id = settings.HF_MODEL_ID or "meta-llama/Llama-3.1-8B-Instruct"
        self.base_url = "https://api-inference.huggingface.co/models"

    def is_configured(self) -> bool:
        return bool(self.token and self.token.strip())

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1024
    ) -> str:
        if not self.is_configured():
            raise LLMConfigurationError(self.name, "HF_TOKEN is not set.")

        prompt = "\n".join([f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>" for m in messages]) + "\n<|im_start|>assistant\n"
        headers = {
            "Authorization": f"Bearer {self.token.strip()}",
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": max(0.01, temperature),
                "max_new_tokens": max_tokens,
                "return_full_text": False
            }
        }

        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
                res = await client.post(f"{self.base_url}/{self.model_id}", headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    return data[0].get("generated_text", "").strip()
                elif isinstance(data, dict):
                    return data.get("generated_text", "").strip()
                return str(data)
        except Exception as e:
            logger.error("Hugging Face API request failed: %s", str(e))
            raise LLMExecutionError(self.name, "Hugging Face Inference failure") from e

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
        if not self.is_configured():
            return {
                "provider": self.name,
                "configured": False,
                "reachable": False,
                "detail": "HF_TOKEN is not configured in environment."
            }
        try:
            headers = {"Authorization": f"Bearer {self.token.strip()}"}
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.get(f"https://huggingface.co/api/models/{self.model_id}", headers=headers)
                return {
                    "provider": self.name,
                    "configured": True,
                    "reachable": res.status_code == 200,
                    "model": self.model_id
                }
        except Exception:
            return {"provider": self.name, "configured": True, "reachable": False}
