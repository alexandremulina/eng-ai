import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


async def test_protected_route_without_token_returns_403():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/npsh", json={
            "p_atm_kpa": 101.325,
            "p_vapor_kpa": 2.338,
            "z_s_m": 5.0,
            "h_loss_m": 2.0,
            "fluid_density_kg_m3": 998.2,
        })
    assert response.status_code == 403 or response.status_code == 401  # HTTPBearer returns 403 or 401 depending on version


async def test_protected_route_with_invalid_token_returns_401():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/calculations/npsh",
            json={
                "p_atm_kpa": 101.325,
                "p_vapor_kpa": 2.338,
                "z_s_m": 5.0,
                "h_loss_m": 2.0,
                "fluid_density_kg_m3": 998.2,
            },
            headers={"Authorization": "Bearer invalid-token-here"},
        )
    assert response.status_code == 401
