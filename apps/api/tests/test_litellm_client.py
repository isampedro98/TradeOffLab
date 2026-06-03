import json
from unittest.mock import MagicMock, patch

import httpx
import pytest
from pydantic import BaseModel, ConfigDict

from app.services.litellm_client import LiteLLMClient, LiteLLMError


class SampleStructuredOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str


def _completion_response(content: dict) -> dict:
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(content),
                }
            }
        ]
    }


def _raw_completion_response(content: str) -> dict:
    return {
        "choices": [
            {
                "message": {
                    "content": content,
                }
            }
        ]
    }


@patch("httpx.post")
def test_generate_structured_sends_strict_json_schema_request(mock_post: MagicMock) -> None:
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=MagicMock(),
        json=lambda: _completion_response({"answer": "structured"}),
    )
    client = LiteLLMClient(
        base_url="http://litellm.test",
        api_key="test-key",
        model="tradeofflab-test",
        timeout_seconds=5.0,
    )
    client.response_format_strategy = "json_schema"

    result = client.generate_structured(
        messages=[{"role": "user", "content": "Return JSON."}],
        response_model=SampleStructuredOutput,
        temperature=0.1,
    )

    assert result.answer == "structured"
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["json"]["model"] == "tradeofflab-test"
    assert call_kwargs["json"]["temperature"] == 0.1
    assert call_kwargs["json"]["num_retries"] == 0
    assert call_kwargs["timeout"] == 5.0
    response_format = call_kwargs["json"]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["name"] == "SampleStructuredOutput"
    assert response_format["json_schema"]["strict"] is True
    assert "answer" in response_format["json_schema"]["schema"]["properties"]
    assert call_kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert mock_post.call_args.args[0] == "http://litellm.test/v1/chat/completions"


@patch("httpx.post")
def test_generate_structured_supports_per_call_timeout_override(mock_post: MagicMock) -> None:
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=MagicMock(),
        json=lambda: _completion_response({"answer": "override-timeout"}),
    )
    client = LiteLLMClient(
        base_url="http://litellm.test",
        api_key="test-key",
        model="tradeofflab-test",
        timeout_seconds=30.0,
    )

    result = client.generate_structured(
        messages=[{"role": "user", "content": "Return JSON."}],
        response_model=SampleStructuredOutput,
        timeout_seconds=7.5,
    )

    assert result.answer == "override-timeout"
    assert mock_post.call_args.kwargs["timeout"] == 7.5


@patch("httpx.post")
def test_generate_structured_raises_on_http_error(mock_post: MagicMock) -> None:
    response = MagicMock(status_code=429)
    mock_post.return_value = response
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "rate limited",
        request=MagicMock(),
        response=response,
    )
    client = LiteLLMClient(
        base_url="http://litellm.test",
        api_key="test-key",
        model="tradeofflab-test",
    )

    with pytest.raises(LiteLLMError) as error:
        client.generate_structured(
            messages=[{"role": "user", "content": "Return JSON."}],
            response_model=SampleStructuredOutput,
        )

    assert error.value.status_code == 429


@patch("httpx.post")
def test_generate_structured_supports_json_object_strategy(mock_post: MagicMock) -> None:
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=MagicMock(),
        json=lambda: _completion_response({"answer": "object-mode"}),
    )
    client = LiteLLMClient(
        base_url="http://litellm.test",
        api_key="test-key",
        model="tradeofflab-test",
    )
    client.response_format_strategy = "json_object"

    result = client.generate_structured(
        messages=[{"role": "user", "content": "Return JSON."}],
        response_model=SampleStructuredOutput,
    )

    assert result.answer == "object-mode"
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["json"]["response_format"] == {"type": "json_object"}
    assert call_kwargs["json"]["messages"][0]["role"] == "system"
    assert "JSON Schema" in call_kwargs["json"]["messages"][0]["content"]


@patch("httpx.post")
def test_generate_structured_raises_on_empty_content(mock_post: MagicMock) -> None:
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=MagicMock(),
        json=lambda: {"choices": [{"message": {"content": "   "}}]},
    )
    client = LiteLLMClient(
        base_url="http://litellm.test",
        api_key="test-key",
        model="tradeofflab-test",
    )

    with pytest.raises(LiteLLMError, match="empty structured content"):
        client.generate_structured(
            messages=[{"role": "user", "content": "Return JSON."}],
            response_model=SampleStructuredOutput,
        )


@patch("httpx.post")
def test_generate_structured_raises_on_invalid_json(mock_post: MagicMock) -> None:
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=MagicMock(),
        json=lambda: {"choices": [{"message": {"content": "not-json"}}]},
    )
    client = LiteLLMClient(
        base_url="http://litellm.test",
        api_key="test-key",
        model="tradeofflab-test",
    )

    with pytest.raises(LiteLLMError, match="non-JSON content"):
        client.generate_structured(
            messages=[{"role": "user", "content": "Return JSON."}],
            response_model=SampleStructuredOutput,
        )


@patch("httpx.post")
def test_generate_structured_extracts_json_from_markdown_fence(mock_post: MagicMock) -> None:
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=MagicMock(),
        json=lambda: _raw_completion_response('```json\n{"answer":"fenced"}\n```'),
    )
    client = LiteLLMClient(
        base_url="http://litellm.test",
        api_key="test-key",
        model="tradeofflab-test",
    )

    result = client.generate_structured(
        messages=[{"role": "user", "content": "Return JSON."}],
        response_model=SampleStructuredOutput,
    )

    assert result.answer == "fenced"


@patch("httpx.post")
def test_generate_structured_extracts_json_from_text_wrapper(mock_post: MagicMock) -> None:
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=MagicMock(),
        json=lambda: _raw_completion_response('Here is the result: {"answer":"wrapped"} Thanks.'),
    )
    client = LiteLLMClient(
        base_url="http://litellm.test",
        api_key="test-key",
        model="tradeofflab-test",
    )

    result = client.generate_structured(
        messages=[{"role": "user", "content": "Return JSON."}],
        response_model=SampleStructuredOutput,
    )

    assert result.answer == "wrapped"


@patch("httpx.post")
def test_generate_structured_raises_on_schema_validation_failure(mock_post: MagicMock) -> None:
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=MagicMock(),
        json=lambda: _completion_response({"unexpected": "field"}),
    )
    client = LiteLLMClient(
        base_url="http://litellm.test",
        api_key="test-key",
        model="tradeofflab-test",
    )

    with pytest.raises(LiteLLMError, match="failed schema validation"):
        client.generate_structured(
            messages=[{"role": "user", "content": "Return JSON."}],
            response_model=SampleStructuredOutput,
        )
