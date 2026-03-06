import httpx
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.ai import call_llm, call_vision_llm, MODELS


async def test_call_llm_uses_correct_model_for_task():
    """Each task maps to the right model."""
    with patch("app.services.ai.httpx.AsyncClient") as mock_client_cls:
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "test response"}}]}
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        with patch("app.services.ai.get_settings") as mock_settings:
            mock_settings.return_value.openrouter_api_key = "test-key"
            result = await call_llm([{"role": "user", "content": "hello"}], task="reasoning")

        assert result == "test response"
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["model"] == MODELS["reasoning"]


async def test_call_llm_falls_back_to_fallback_model_for_unknown_task():
    with patch("app.services.ai.httpx.AsyncClient") as mock_client_cls:
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        with patch("app.services.ai.get_settings") as mock_settings:
            mock_settings.return_value.openrouter_api_key = "test-key"
            await call_llm([{"role": "user", "content": "hi"}], task="unknown_task")

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["model"] == MODELS["fallback"]


async def test_call_vision_llm_uses_vision_task():
    with patch("app.services.ai.call_llm", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "diagnosis result"
        result = await call_vision_llm("base64data", "analyze this image")
    assert result == "diagnosis result"
    mock_call.assert_called_once()
    call_args = mock_call.call_args
    assert call_args[1]["task"] == "vision"
    messages = call_args[0][0]
    image_parts = [p for p in messages[0]["content"] if isinstance(p, dict) and p.get("type") == "image_url"]
    assert len(image_parts) == 1
    assert "base64data" in image_parts[0]["image_url"]["url"]
    assert "image/jpeg" in image_parts[0]["image_url"]["url"]  # default MIME type


async def test_call_llm_raises_on_http_error():
    with patch("app.services.ai.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock(status_code=500)
        )
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        with patch("app.services.ai.get_settings") as mock_settings:
            mock_settings.return_value.openrouter_api_key = "test-key"
            with pytest.raises(httpx.HTTPStatusError):
                await call_llm([{"role": "user", "content": "hi"}])


def test_models_dict_has_all_required_tasks():
    required = {"reasoning", "rag", "vision", "report", "fallback"}
    assert required.issubset(set(MODELS.keys()))


async def test_call_llm_raises_when_no_api_key():
    with patch("app.services.ai.get_settings") as mock_settings:
        mock_settings.return_value.openrouter_api_key = None
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY is not configured"):
            await call_llm([{"role": "user", "content": "hi"}])
