import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

PUMP_A_POINTS = [
    {"q": 0, "h": 50}, {"q": 10, "h": 45},
    {"q": 20, "h": 35}, {"q": 30, "h": 20},
]
PUMP_B_POINTS = [
    {"q": 0, "h": 40}, {"q": 8, "h": 35},
    {"q": 16, "h": 25}, {"q": 24, "h": 10},
]


@pytest.mark.asyncio
async def test_parallel_pumps_two_pumps(mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/parallel-pumps", json={
            "pumps": [
                {"name": "Pump A", "points": PUMP_A_POINTS, "bep_q": 18.0},
                {"name": "Pump B", "points": PUMP_B_POINTS, "bep_q": 12.0},
            ],
            "system_curve": {"static_head": 5.0, "resistance": 0.04},
        })
    assert response.status_code == 200
    data = response.json()
    assert "operating_point" in data
    assert data["operating_point"]["q_total"] > 0
    assert data["operating_point"]["h"] > 5
    assert len(data["pumps"]) == 2
    assert len(data["combined_curve_points"]) > 5
    assert len(data["system_curve_points"]) > 5


@pytest.mark.asyncio
async def test_parallel_pumps_no_intersection_returns_400(mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/parallel-pumps", json={
            "pumps": [
                {"name": "Weak", "points": [
                    {"q": 0, "h": 10}, {"q": 5, "h": 7}, {"q": 10, "h": 2},
                ], "bep_q": 5.0},
            ],
            "system_curve": {"static_head": 50.0, "resistance": 0.01},
        })
    assert response.status_code == 400
    assert "no_intersection" in response.json()["detail"]


@pytest.mark.asyncio
async def test_parallel_pumps_too_few_points_returns_400(mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/parallel-pumps", json={
            "pumps": [
                {"name": "A", "points": [{"q": 0, "h": 50}], "bep_q": 10.0},
            ],
            "system_curve": {"static_head": 5.0, "resistance": 0.04},
        })
    # min_length=3 on PumpInputModel causes Pydantic to reject at schema level (422)
    assert response.status_code in (400, 422)
