import pytest
from app.services.head_loss import calculate_head_loss, HeadLossResult
from httpx import AsyncClient, ASGITransport
from app.main import app


def test_turbulent_water_steel_pipe():
    """Water at 20°C in 100mm steel pipe, 50 m length, 2 m/s velocity."""
    result = calculate_head_loss(
        flow_m3h=56.5,       # ~2 m/s in 100mm pipe
        pipe_diameter_mm=100.0,
        pipe_length_m=50.0,
        pipe_roughness_mm=0.046,  # commercial steel
        fluid_density_kg_m3=998.2,
        fluid_viscosity_cP=1.002,
    )
    assert result.flow_regime == "turbulent"
    # h_f = f*(L/D)*(v²/2g) ≈ 0.0186*(500)*(3.993/19.62) ≈ 1.89 m
    assert 1.5 < result.head_loss_m < 2.5


def test_laminar_regime():
    """Viscous fluid, slow flow — should be laminar."""
    result = calculate_head_loss(
        flow_m3h=1.0,
        pipe_diameter_mm=50.0,
        pipe_length_m=10.0,
        pipe_roughness_mm=0.046,
        fluid_density_kg_m3=900.0,
        fluid_viscosity_cP=100.0,  # viscous oil
    )
    assert result.flow_regime == "laminar"
    assert result.reynolds_number < 2300


def test_result_fields_present():
    """Result dataclass has all required fields."""
    result = calculate_head_loss(
        flow_m3h=56.5,
        pipe_diameter_mm=100.0,
        pipe_length_m=50.0,
        pipe_roughness_mm=0.046,
        fluid_density_kg_m3=998.2,
        fluid_viscosity_cP=1.002,
    )
    assert isinstance(result, HeadLossResult)
    assert result.head_loss_m > 0
    assert result.velocity_m_s > 0
    assert result.reynolds_number > 0
    assert result.friction_factor > 0
    assert result.flow_regime in ("laminar", "turbulent", "transitional")
    assert "h_f" in result.formula


def test_formula_contains_result():
    """Formula string includes the computed head loss value."""
    result = calculate_head_loss(
        flow_m3h=56.5,
        pipe_diameter_mm=100.0,
        pipe_length_m=50.0,
        pipe_roughness_mm=0.046,
        fluid_density_kg_m3=998.2,
        fluid_viscosity_cP=1.002,
    )
    assert str(result.head_loss_m) in result.formula


def test_darcy_weisbach_physics():
    """Doubling pipe length should roughly double head loss."""
    base = calculate_head_loss(
        flow_m3h=20.0,
        pipe_diameter_mm=80.0,
        pipe_length_m=100.0,
        pipe_roughness_mm=0.046,
        fluid_density_kg_m3=998.2,
        fluid_viscosity_cP=1.002,
    )
    doubled = calculate_head_loss(
        flow_m3h=20.0,
        pipe_diameter_mm=80.0,
        pipe_length_m=200.0,
        pipe_roughness_mm=0.046,
        fluid_density_kg_m3=998.2,
        fluid_viscosity_cP=1.002,
    )
    ratio = doubled.head_loss_m / base.head_loss_m
    assert 1.95 < ratio < 2.05


def test_transitional_regime():
    """Flow in Re 2300–4000 range is labelled transitional.

    D=50mm, flow=1.5 m³/h, density=1000 kg/m³, viscosity=3.5 cP -> Re≈3032.
    """
    result = calculate_head_loss(
        flow_m3h=1.5,
        pipe_diameter_mm=50.0,
        pipe_length_m=10.0,
        pipe_roughness_mm=0.046,
        fluid_density_kg_m3=1000.0,
        fluid_viscosity_cP=3.5,
    )
    assert 2300 < result.reynolds_number < 4000, (
        f"Expected Re in transitional range 2300-4000, got {result.reynolds_number}"
    )
    assert result.flow_regime == "transitional"


@pytest.mark.asyncio
async def test_head_loss_endpoint_basic():
    """POST /calculations/head-loss returns correct fields."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/head-loss", json={
            "flow_m3h": 56.5,
            "pipe_diameter_mm": 100.0,
            "pipe_length_m": 50.0,
            "pipe_roughness_mm": 0.046,
            "fluid_density_kg_m3": 998.2,
            "fluid_viscosity_cP": 1.002,
        })
    assert response.status_code == 200
    data = response.json()
    assert 1.5 < data["head_loss_m"] < 2.5
    assert data["flow_regime"] == "turbulent"
    assert data["velocity_m_s"] > 0
    assert data["reynolds_number"] > 0
    assert data["friction_factor"] > 0
    assert "h_f" in data["formula"]


@pytest.mark.asyncio
async def test_head_loss_endpoint_defaults():
    """POST /calculations/head-loss uses sensible defaults for optional fields."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/head-loss", json={
            "flow_m3h": 30.0,
            "pipe_diameter_mm": 80.0,
            "pipe_length_m": 100.0,
        })
    assert response.status_code == 200
    data = response.json()
    assert data["head_loss_m"] > 0


@pytest.mark.asyncio
async def test_head_loss_endpoint_invalid_flow_returns_422():
    """Zero or negative flow should be rejected by Pydantic."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/head-loss", json={
            "flow_m3h": 0.0,
            "pipe_diameter_mm": 100.0,
            "pipe_length_m": 50.0,
        })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_head_loss_endpoint_invalid_diameter_returns_422():
    """Negative diameter should be rejected by Pydantic."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/head-loss", json={
            "flow_m3h": 30.0,
            "pipe_diameter_mm": -10.0,
            "pipe_length_m": 50.0,
        })
    assert response.status_code == 422
