import pytest
from app.services.npsh import calculate_npsha, NPSHResult
from httpx import AsyncClient, ASGITransport
from app.main import app


def test_npsha_basic():
    """Water at 20°C, 5m suction head, 2m losses, atmospheric pressure."""
    result = calculate_npsha(
        p_atm_kpa=101.325,
        p_vapor_kpa=2.338,   # water at 20°C
        z_s_m=5.0,           # suction head (positive = above pump)
        h_loss_m=2.0,        # friction losses in suction line
        fluid_density_kg_m3=998.2,
        g=9.81,
    )
    # NPSHa = (p_atm - p_vapor) / (rho * g) + z_s - h_loss
    # = (101325 - 2338) / (998.2 * 9.81) + 5 - 2
    # ≈ 10.11 + 5 - 2 = 13.11 m
    assert abs(result.npsha_m - 13.11) < 0.1


def test_npsha_negative_suction():
    """Pump above fluid level (negative suction head)."""
    result = calculate_npsha(
        p_atm_kpa=101.325,
        p_vapor_kpa=2.338,
        z_s_m=-3.0,
        h_loss_m=1.5,
        fluid_density_kg_m3=998.2,
        g=9.81,
    )
    assert result.npsha_m < 10.0


def test_cavitation_risk_detected():
    """NPSHa < NPSHr should flag cavitation risk."""
    result = calculate_npsha(
        p_atm_kpa=101.325,
        p_vapor_kpa=70.0,   # high vapor pressure (hot fluid)
        z_s_m=-5.0,
        h_loss_m=3.0,
        fluid_density_kg_m3=980.0,
        g=9.81,
        npshr_m=5.0,
    )
    assert result.cavitation_risk is True


def test_no_cavitation_risk_when_npsha_greater():
    """NPSHa > NPSHr should not flag cavitation risk."""
    result = calculate_npsha(
        p_atm_kpa=101.325,
        p_vapor_kpa=2.338,
        z_s_m=5.0,
        h_loss_m=1.0,
        fluid_density_kg_m3=998.2,
        g=9.81,
        npshr_m=5.0,
    )
    assert result.cavitation_risk is False
    assert result.safety_margin_m is not None
    assert result.safety_margin_m > 0


def test_no_npshr_provided():
    """Without NPSHr, risk is False and safety margin is None."""
    result = calculate_npsha(
        p_atm_kpa=101.325,
        p_vapor_kpa=2.338,
        z_s_m=5.0,
        h_loss_m=2.0,
        fluid_density_kg_m3=998.2,
        g=9.81,
    )
    assert result.cavitation_risk is False
    assert result.safety_margin_m is None
    assert result.npshr_m is None


def test_result_has_formula():
    """Result should include human-readable formula."""
    result = calculate_npsha(
        p_atm_kpa=101.325,
        p_vapor_kpa=2.338,
        z_s_m=5.0,
        h_loss_m=2.0,
        fluid_density_kg_m3=998.2,
        g=9.81,
    )
    assert "NPSHa" in result.formula
    assert str(result.npsha_m) in result.formula


@pytest.mark.asyncio
async def test_npsh_endpoint_basic():
    """POST /calculations/npsh returns correct NPSHa."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/npsh", json={
            "p_atm_kpa": 101.325,
            "p_vapor_kpa": 2.338,
            "z_s_m": 5.0,
            "h_loss_m": 2.0,
            "fluid_density_kg_m3": 998.2,
            "g": 9.81,
        })
    assert response.status_code == 200
    data = response.json()
    assert abs(data["npsha_m"] - 13.11) < 0.1
    assert data["npshr_m"] is None
    assert data["safety_margin_m"] is None
    assert data["cavitation_risk"] is False
    assert "NPSHa" in data["formula"]


@pytest.mark.asyncio
async def test_npsh_endpoint_with_npshr():
    """POST /calculations/npsh with npshr_m returns safety margin and cavitation flag."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/npsh", json={
            "p_atm_kpa": 101.325,
            "p_vapor_kpa": 70.0,
            "z_s_m": -5.0,
            "h_loss_m": 3.0,
            "fluid_density_kg_m3": 980.0,
            "g": 9.81,
            "npshr_m": 5.0,
        })
    assert response.status_code == 200
    data = response.json()
    assert data["cavitation_risk"] is True
    assert data["npshr_m"] == 5.0
    assert data["safety_margin_m"] is not None
    assert data["safety_margin_m"] < 0
