import pytest
from app.services.units import convert_unit, ConversionError


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
