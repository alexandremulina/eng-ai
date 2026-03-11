import pytest
from app.services.material_selection import select_materials
from httpx import AsyncClient, ASGITransport
from app.main import app


def test_sulfuric_acid_cast_iron_incompatible():
    result = select_materials(fluid="sulfuric_acid", concentration_pct=10.0, temp_c=25.0)
    casing = next(r for r in result if r.component == "casing")
    cast_iron = next(m for m in casing.materials if m.material == "Cast Iron")
    assert cast_iron.rating == "incompatible"


def test_water_cast_iron_recommended():
    result = select_materials(fluid="water", concentration_pct=100.0, temp_c=20.0)
    casing = next(r for r in result if r.component == "casing")
    cast_iron = next(m for m in casing.materials if m.material == "Cast Iron")
    assert cast_iron.rating == "recommended"


def test_returns_all_components():
    result = select_materials(fluid="water", concentration_pct=100.0, temp_c=20.0)
    components = {r.component for r in result}
    assert "casing" in components
    assert "impeller" in components
    assert "wear_ring" in components
    assert "shaft" in components
    assert "mechanical_seal" in components


def test_unknown_fluid_raises():
    with pytest.raises(ValueError, match="Unknown fluid"):
        select_materials(fluid="__unknown__", concentration_pct=50.0, temp_c=20.0)


def test_carbon_steel_caustic_soda_below_60c_recommended():
    result = select_materials(fluid="caustic_soda", concentration_pct=50.0, temp_c=40.0)
    casing = next(r for r in result if r.component == "casing")
    cs = next(m for m in casing.materials if m.material == "Carbon Steel")
    assert cs.rating == "recommended"


def test_carbon_steel_caustic_soda_above_60c_incompatible():
    result = select_materials(fluid="caustic_soda", concentration_pct=50.0, temp_c=80.0)
    casing = next(r for r in result if r.component == "casing")
    cs = next(m for m in casing.materials if m.material == "Carbon Steel")
    assert cs.rating == "incompatible"


def test_carbon_steel_caustic_soda_above_60c_has_note():
    result = select_materials(fluid="caustic_soda", concentration_pct=50.0, temp_c=80.0)
    casing = next(r for r in result if r.component == "casing")
    cs = next(m for m in casing.materials if m.material == "Carbon Steel")
    assert "60" in cs.note


def test_sulfuric_acid_ss316_mid_concentration_incompatible():
    result = select_materials(fluid="sulfuric_acid", concentration_pct=30.0, temp_c=25.0)
    casing = next(r for r in result if r.component == "casing")
    ss316 = next(m for m in casing.materials if m.material == "SS 316")
    assert ss316.rating == "incompatible"


def test_sulfuric_acid_ss316_low_concentration_conditional():
    result = select_materials(fluid="sulfuric_acid", concentration_pct=3.0, temp_c=25.0)
    casing = next(r for r in result if r.component == "casing")
    ss316 = next(m for m in casing.materials if m.material == "SS 316")
    assert ss316.rating == "conditional"


def test_nbr_caustic_soda_above_40c_incompatible():
    result = select_materials(fluid="caustic_soda", concentration_pct=50.0, temp_c=50.0)
    orings = next(r for r in result if r.component == "o_rings")
    nbr = next(m for m in orings.materials if m.material == "NBR")
    assert nbr.rating == "incompatible"


def test_water_carbon_steel_casing_present():
    result = select_materials(fluid="water", concentration_pct=100.0, temp_c=25.0)
    casing = next(r for r in result if r.component == "casing")
    materials = [m.material for m in casing.materials]
    assert "Carbon Steel" in materials


@pytest.mark.asyncio
async def test_material_selection_endpoint(mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/material-selection", json={
            "fluid": "water",
            "concentration_pct": 100.0,
            "temp_c": 25.0,
        })
    assert response.status_code == 200
    data = response.json()
    assert data["fluid"] == "water"
    assert len(data["components"]) > 0
    first = data["components"][0]
    assert "component" in first
    assert "materials" in first
    assert len(first["materials"]) > 0
    assert "rating" in first["materials"][0]


@pytest.mark.asyncio
async def test_material_selection_unknown_fluid_returns_400(mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/material-selection", json={
            "fluid": "not_a_real_fluid",
            "concentration_pct": 50.0,
            "temp_c": 20.0,
        })
    assert response.status_code == 400
    assert "Unknown fluid" in response.json()["detail"]
