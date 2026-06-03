from typing import Any

from pydantic import BaseModel

from app.services.litellm_client import LiteLLMClient


class StubLiteLLMClient(LiteLLMClient):
    """Records structured-generation calls and returns preconfigured payloads."""

    def __init__(
        self,
        *,
        responses: dict[type[BaseModel], BaseModel | list[BaseModel]] | None = None,
        model: str = "test-model",
    ) -> None:
        super().__init__(
            base_url="http://litellm.test",
            api_key="test-key",
            model=model,
            timeout_seconds=1.0,
        )
        self.responses = responses or {}
        self.calls: list[dict[str, Any]] = []

    def generate_structured(
        self,
        *,
        messages: list[dict[str, Any]],
        response_model: type[BaseModel],
        temperature: float = 0.2,
        max_tokens: int | None = None,
        allow_repair: bool = True,
        timeout_seconds: float | None = None,
    ) -> BaseModel:
        self.calls.append(
            {
                "messages": messages,
                "response_model": response_model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "allow_repair": allow_repair,
                "timeout_seconds": timeout_seconds,
            }
        )
        if response_model not in self.responses:
            raise KeyError(f"No stub response registered for {response_model.__name__}")
        response = self.responses[response_model]
        if isinstance(response, list):
            if not response:
                raise KeyError(f"No remaining stub responses registered for {response_model.__name__}")
            return response.pop(0)
        return response
