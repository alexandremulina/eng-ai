import pytest
import json
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.diagnosis import diagnose_component

MOCK_DIAGNOSIS = {
    "component": "mechanical seal",
    "root_cause": "corrosion",
    "severity": "high",
    "confidence": "high",
    "immediate_action": "Replace seal immediately",
    "preventive_action": "Use corrosion-resistant materials",
    "possible_causes": ["chemical attack", "improper installation"],
    "disclaimer": "This is an AI-assisted diagnosis. Always validate with certified inspection.",
}


async def test_diagnose_component_returns_parsed_json():
    mock_vision_response = json.dumps(MOCK_DIAGNOSIS)
    with patch("app.services.diagnosis.call_vision_llm", new_callable=AsyncMock, return_value=mock_vision_response):
        result = await diagnose_component(b"fake_image_bytes", notes="Seal from pump XY-01")
    assert result["component"] == "mechanical seal"
    assert result["severity"] == "high"
    assert "disclaimer" in result


async def test_diagnose_component_handles_markdown_wrapped_json():
    """LLM sometimes wraps JSON in markdown code blocks."""
    mock_vision_response = f"```json\n{json.dumps(MOCK_DIAGNOSIS)}\n```"
    with patch("app.services.diagnosis.call_vision_llm", new_callable=AsyncMock, return_value=mock_vision_response):
        result = await diagnose_component(b"fake_image_bytes")
    assert result["component"] == "mechanical seal"


async def test_diagnose_component_returns_fallback_on_invalid_json():
    with patch("app.services.diagnosis.call_vision_llm", new_callable=AsyncMock, return_value="not valid json at all"):
        result = await diagnose_component(b"fake_image_bytes")
    assert result["component"] == "Unknown"
    assert result["confidence"] == "low"
    assert "disclaimer" in result


async def test_analyze_endpoint_requires_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/diagnosis/analyze", files={"file": ("test.jpg", b"data", "image/jpeg")})
    assert response.status_code in (401, 403)


async def test_analyze_endpoint_rejects_invalid_mime_type(mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/diagnosis/analyze",
            files={"file": ("test.pdf", b"pdf data", "application/pdf")},
            headers={"Authorization": "Bearer test-token"},
        )
    assert response.status_code == 422


async def test_analyze_endpoint_rejects_oversized_file(mock_user):
    big_image = b"x" * (11 * 1024 * 1024)  # 11 MB
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/diagnosis/analyze",
            files={"file": ("test.jpg", big_image, "image/jpeg")},
            headers={"Authorization": "Bearer test-token"},
        )
    assert response.status_code == 413


async def test_analyze_endpoint_returns_diagnosis(mock_user):
    with patch("app.routers.diagnosis.diagnose_component", new_callable=AsyncMock, return_value=MOCK_DIAGNOSIS), \
         patch("app.routers.diagnosis.check_and_record_usage"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/diagnosis/analyze",
                files={"file": ("test.jpg", b"fake image", "image/jpeg")},
                data={"notes": "Seal looks corroded"},
                headers={"Authorization": "Bearer test-token"},
            )
    assert response.status_code == 200
    data = response.json()
    assert data["component"] == "mechanical seal"
    assert data["severity"] == "high"
