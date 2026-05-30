import json
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from app.core.config import settings

ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


class LiteLLMError(RuntimeError):
    """Raised when the LiteLLM proxy call fails or returns invalid content."""

    def __init__(self, message: str, *, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


class LiteLLMClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (base_url or settings.litellm_base_url).rstrip("/")
        self.api_key = api_key or settings.litellm_api_key
        self.model = model or settings.litellm_model
        self.timeout_seconds = timeout_seconds or settings.litellm_timeout_seconds

    def generate_structured(
        self,
        *,
        messages: list[dict[str, Any]],
        response_model: type[ResponseModelT],
        temperature: float = 0.2,
    ) -> ResponseModelT:
        payload = {
            "model": self.model,
            "temperature": temperature,
            "num_retries": 0,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "strict": True,
                    "schema": response_model.model_json_schema(),
                },
            },
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise LiteLLMError(
                f"LiteLLM request failed: {error}",
                status_code=error.response.status_code,
            ) from error
        except httpx.HTTPError as error:
            raise LiteLLMError(f"LiteLLM request failed: {error}") from error

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise LiteLLMError("LiteLLM response did not include message content.") from error

        if not isinstance(content, str) or not content.strip():
            raise LiteLLMError("LiteLLM returned empty structured content.")

        try:
            parsed_content = json.loads(content)
        except json.JSONDecodeError as error:
            raise LiteLLMError("LiteLLM returned non-JSON content.") from error

        try:
            return response_model.model_validate(parsed_content)
        except Exception as error:
            raise LiteLLMError("LiteLLM returned content that failed schema validation.") from error
