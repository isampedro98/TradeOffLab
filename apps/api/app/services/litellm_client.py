import json
import time
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
        self.response_format_strategy = settings.litellm_response_format_strategy

    def generate_structured(
        self,
        *,
        messages: list[dict[str, Any]],
        response_model: type[ResponseModelT],
        temperature: float = 0.2,
        max_tokens: int | None = None,
        allow_repair: bool = True,
    ) -> ResponseModelT:
        payload_messages = messages
        payload = {
            "model": self.model,
            "temperature": temperature,
            "num_retries": 0,
            "messages": payload_messages,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        schema = response_model.model_json_schema()
        if self.response_format_strategy == "json_object":
            payload["messages"] = self._build_json_object_messages(
                messages=messages,
                response_model=response_model,
                schema=schema,
            )
            payload["response_format"] = {"type": "json_object"}
        else:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "strict": True,
                    "schema": schema,
                },
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = self._post_with_retries(
            headers=headers,
            payload=payload,
        )

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
            json_candidate = self._extract_json_candidate(content)
            if json_candidate is None:
                raise LiteLLMError("LiteLLM returned non-JSON content.") from error
            try:
                parsed_content = json.loads(json_candidate)
            except json.JSONDecodeError as nested_error:
                raise LiteLLMError("LiteLLM returned non-JSON content.") from nested_error

        try:
            return response_model.model_validate(parsed_content)
        except Exception as error:
            if allow_repair:
                try:
                    return self._repair_structured_output(
                        parsed_content=parsed_content,
                        response_model=response_model,
                    )
                except LiteLLMError:
                    pass
            raise LiteLLMError("LiteLLM returned content that failed schema validation.") from error

    def _post_with_retries(
        self,
        *,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> httpx.Response:
        last_error: Exception | None = None
        retry_delays = (0.0, 0.75, 1.5)

        for attempt, delay_seconds in enumerate(retry_delays, start=1):
            if delay_seconds > 0:
                time.sleep(delay_seconds)
            try:
                response = httpx.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as error:
                if not self._is_retryable_status(error.response.status_code) or attempt == len(
                    retry_delays
                ):
                    raise LiteLLMError(
                        f"LiteLLM request failed: {error}",
                        status_code=error.response.status_code,
                    ) from error
                last_error = error
            except httpx.HTTPError as error:
                if not self._is_retryable_transport_error(error) or attempt == len(retry_delays):
                    raise LiteLLMError(f"LiteLLM request failed: {error}") from error
                last_error = error

        if isinstance(last_error, httpx.HTTPStatusError):
            raise LiteLLMError(
                f"LiteLLM request failed: {last_error}",
                status_code=last_error.response.status_code,
            ) from last_error
        if isinstance(last_error, httpx.HTTPError):
            raise LiteLLMError(f"LiteLLM request failed: {last_error}") from last_error
        raise LiteLLMError("LiteLLM request failed without a recoverable response.")

    @staticmethod
    def _build_json_object_messages(
        *,
        messages: list[dict[str, Any]],
        response_model: type[BaseModel],
        schema: dict[str, Any],
    ) -> list[dict[str, Any]]:
        schema_instruction = (
            "Return one JSON object only. Do not wrap it in markdown. "
            "The first character of the response must be '{' and the last character must be '}'. "
            f"It must validate against this JSON Schema for {response_model.__name__}:\n"
            f"{json.dumps(schema, indent=2)}"
        )
        if not messages:
            return [{"role": "system", "content": schema_instruction}]

        updated_messages = [dict(message) for message in messages]
        first_message = updated_messages[0]
        if first_message.get("role") == "system":
            first_content = str(first_message.get("content", "")).strip()
            first_message["content"] = (
                f"{first_content}\n\n{schema_instruction}" if first_content else schema_instruction
            )
        else:
            updated_messages.insert(0, {"role": "system", "content": schema_instruction})
        return updated_messages

    @staticmethod
    def _extract_json_candidate(content: str) -> str | None:
        stripped = content.strip()
        if stripped.startswith("```"):
            fence_lines = stripped.splitlines()
            if len(fence_lines) >= 3 and fence_lines[-1].strip() == "```":
                fenced_body = "\n".join(fence_lines[1:-1]).strip()
                if fenced_body.lower().startswith("json"):
                    fenced_body = fenced_body[4:].strip()
                if fenced_body:
                    return fenced_body

        object_start = stripped.find("{")
        object_end = stripped.rfind("}")
        if object_start != -1 and object_end != -1 and object_start < object_end:
            return stripped[object_start : object_end + 1]
        return None

    @staticmethod
    def _is_retryable_status(status_code: int) -> bool:
        return status_code in {408, 429, 500, 502, 503, 504}

    @staticmethod
    def _is_retryable_transport_error(error: httpx.HTTPError) -> bool:
        return isinstance(error, (httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError))

    def _repair_structured_output(
        self,
        *,
        parsed_content: Any,
        response_model: type[ResponseModelT],
    ) -> ResponseModelT:
        repair_messages = [
            {
                "role": "system",
                "content": (
                    "Repair the supplied JSON so it matches the required schema exactly. "
                    "Return only one JSON object. Do not add commentary."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Required schema for {response_model.__name__}:\n"
                    f"{json.dumps(response_model.model_json_schema(), indent=2)}\n\n"
                    f"JSON to repair:\n{json.dumps(parsed_content, indent=2)}"
                ),
            },
        ]
        return self.generate_structured(
            messages=repair_messages,
            response_model=response_model,
            temperature=0.0,
            max_tokens=900,
            allow_repair=False,
        )
