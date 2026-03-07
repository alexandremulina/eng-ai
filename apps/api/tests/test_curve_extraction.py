import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_extract_curve_returns_points(mock_user):
    """Mock vision LLM returns valid H-Q points from an uploaded image."""
    fake_llm_response = '[{"q": 0, "h": 50}, {"q": 10, "h": 42}, {"q": 20, "h": 30}, {"q": 30, "h": 12}]'

    with patch("app.routers.calculations.call_vision_llm", new_callable=AsyncMock, return_value=fake_llm_response):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/calculations/extract-pump-curve",
                files={"file": ("curve.png", b"fake-image-bytes", "image/png")},
            )
    assert response.status_code == 200
    data = response.json()
    assert "points" in data
    assert len(data["points"]) == 4
    assert data["points"][0]["q"] == 0
    assert data["points"][0]["h"] == 50


@pytest.mark.asyncio
async def test_extract_curve_invalid_llm_response_returns_400(mock_user):
    """If LLM returns garbage, endpoint returns 400."""
    with patch("app.routers.calculations.call_vision_llm", new_callable=AsyncMock, return_value="not valid json"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/calculations/extract-pump-curve",
                files={"file": ("curve.png", b"fake-image-bytes", "image/png")},
            )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_extract_curve_strips_markdown_fences(mock_user):
    """LLM response wrapped in markdown code fences is parsed correctly."""
    fenced = '```json\n[{"q": 0, "h": 45}, {"q": 10, "h": 38}, {"q": 20, "h": 28}]\n```'

    with patch("app.routers.calculations.call_vision_llm", new_callable=AsyncMock, return_value=fenced):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/calculations/extract-pump-curve",
                files={"file": ("curve.png", b"fake-image-bytes", "image/png")},
            )
    assert response.status_code == 200
    data = response.json()
    assert len(data["points"]) == 3


@pytest.mark.asyncio
async def test_extract_curve_too_few_points_returns_400(mock_user):
    """LLM returning fewer than 3 points should return 400."""
    too_few = '[{"q": 0, "h": 50}, {"q": 10, "h": 40}]'  # only 2 points

    with patch("app.routers.calculations.call_vision_llm", new_callable=AsyncMock, return_value=too_few):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/calculations/extract-pump-curve",
                files={"file": ("curve.png", b"fake-image-bytes", "image/png")},
            )
    assert response.status_code == 400
    assert "Could not extract curve" in response.json()["detail"]
