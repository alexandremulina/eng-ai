import pytest
from app.services.units import convert_unit, ConversionError
from httpx import AsyncClient, ASGITransport
from app.main import app


def test_flow_gpm_to_m3h():
    result = convert_unit(100, "gpm", "m3/h")
    assert abs(result - 22.7125) < 0.001


def test_pressure_psi_to_bar():
    result = convert_unit(100, "psi", "bar")
    assert abs(result - 6.8948) < 0.0001


def test_pressure_psi_to_kpa():
    result = convert_unit(100, "psi", "kPa")
    assert abs(result - 689.476) < 0.01


def test_invalid_conversion_raises():
    with pytest.raises(ConversionError):
        convert_unit(100, "gpm", "bar")  # flow to pressure — incompatible


def test_temperature_celsius_to_fahrenheit():
    result = convert_unit(100, "degC", "degF")
    assert abs(result - 212.0) < 0.001


@pytest.mark.asyncio
async def test_convert_endpoint_success(mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/convert", json={
            "value": 100,
            "from_unit": "psi",
            "to_unit": "bar",
            "decimals": 4
        })
    assert response.status_code == 200
    data = response.json()
    assert abs(data["result"] - 6.8948) < 0.001


@pytest.mark.asyncio
async def test_convert_endpoint_incompatible_units_returns_400(mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/convert", json={
            "value": 100,
            "from_unit": "gpm",
            "to_unit": "bar"
        })
    assert response.status_code == 400
