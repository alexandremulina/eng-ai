import pytest
from app.services.fluid_properties import get_fluid_properties, AVAILABLE_FLUIDS
from httpx import AsyncClient, ASGITransport
from app.main import app


def test_water_at_20c():
    props = get_fluid_properties("water", 20.0)
    assert abs(props.density_kg_m3 - 998.2) < 1.0
    assert abs(props.vapor_pressure_kpa - 2.338) < 0.1


def test_water_at_100c():
    props = get_fluid_properties("water", 100.0)
    assert abs(props.density_kg_m3 - 958.4) < 1.0
    assert abs(props.vapor_pressure_kpa - 101.325) < 1.0


def test_water_at_60c():
    props = get_fluid_properties("water", 60.0)
    assert abs(props.density_kg_m3 - 983.2) < 2.0
    assert abs(props.vapor_pressure_kpa - 19.94) < 1.0


def test_water_interpolates_between_points():
    props = get_fluid_properties("water", 25.0)
    assert 995 < props.density_kg_m3 < 999
    assert 2.3 < props.vapor_pressure_kpa < 4.0


def test_diesel_at_25c():
    props = get_fluid_properties("diesel", 25.0)
    assert 820 < props.density_kg_m3 < 860
    assert props.vapor_pressure_kpa < 1.0


def test_unknown_fluid_raises():
    with pytest.raises(ValueError, match="Unknown fluid"):
        get_fluid_properties("__unknown__", 25.0)


def test_available_fluids():
    assert "water" in AVAILABLE_FLUIDS
    assert "diesel" in AVAILABLE_FLUIDS
    assert "seawater" in AVAILABLE_FLUIDS


@pytest.mark.asyncio
async def test_fluid_properties_endpoint(mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/fluid-properties", json={
            "fluid": "water",
            "temp_c": 20.0,
        })
    assert response.status_code == 200
    data = response.json()
    assert abs(data["density_kg_m3"] - 998.2) < 1.0
    assert abs(data["vapor_pressure_kpa"] - 2.338) < 0.1
    assert "water" in data["available_fluids"]


@pytest.mark.asyncio
async def test_fluid_properties_unknown_fluid_returns_400(mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/fluid-properties", json={
            "fluid": "lava",
            "temp_c": 20.0,
        })
    assert response.status_code == 400
