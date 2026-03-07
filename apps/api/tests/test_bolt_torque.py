import pytest
from app.services.bolt_torque import calculate_bolt_torque, BoltTorqueResult
from httpx import AsyncClient, ASGITransport
from app.main import app


def test_b7_m20_dry():
    """ASTM A193 B7, M20 (20mm), dry condition."""
    result = calculate_bolt_torque(grade="ASTM A193 B7", diameter_mm=20.0, condition="dry")
    assert result.torque_nm > 0
    assert result.torque_ftlb > 0
    assert result.preload_kn > 0
    assert 200 < result.torque_nm < 700


def test_lubricated_less_torque_than_dry():
    """Lubricated gives less torque than dry for same bolt (lower K factor)."""
    dry = calculate_bolt_torque(grade="ISO 8.8", diameter_mm=16.0, condition="dry")
    lubricated = calculate_bolt_torque(grade="ISO 8.8", diameter_mm=16.0, condition="lubricated")
    assert lubricated.torque_nm < dry.torque_nm


def test_unknown_grade_raises():
    with pytest.raises(ValueError, match="Unknown grade"):
        calculate_bolt_torque(grade="FAKE XYZ", diameter_mm=20.0, condition="dry")


def test_result_includes_all_fields():
    result = calculate_bolt_torque(grade="ISO 10.9", diameter_mm=24.0, condition="dry")
    assert result.torque_nm > 0
    assert result.torque_ftlb > 0
    assert result.preload_kn > 0
    assert result.proof_load_mpa > 0
    assert result.grade == "ISO 10.9"
    assert result.diameter_mm == 24.0


@pytest.mark.asyncio
async def test_bolt_torque_endpoint(mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/bolt-torque", json={
            "grade": "ASTM A193 B7",
            "diameter_mm": 20.0,
            "condition": "dry",
        })
    assert response.status_code == 200
    data = response.json()
    assert data["torque_nm"] > 0
    assert data["torque_ftlb"] > 0
    assert data["preload_kn"] > 0
    assert data["proof_load_mpa"] == 862


@pytest.mark.asyncio
async def test_bolt_torque_endpoint_unknown_grade_returns_400(mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/bolt-torque", json={
            "grade": "FAKE",
            "diameter_mm": 20.0,
            "condition": "dry",
        })
    assert response.status_code == 400
