from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FluidProperties:
    fluid: str
    temp_c: float
    density_kg_m3: float
    vapor_pressure_kpa: float


# Water properties: (temp_c, density_kg_m3, vapor_pressure_kpa)
# Source: engineering steam tables
_WATER_TABLE: list[tuple[float, float, float]] = [
    (5.0, 999.9, 0.872),
    (10.0, 999.7, 1.228),
    (15.0, 999.1, 1.705),
    (20.0, 998.2, 2.338),
    (25.0, 997.0, 3.169),
    (30.0, 995.7, 4.243),
    (40.0, 992.2, 7.384),
    (50.0, 988.1, 12.35),
    (60.0, 983.2, 19.94),
    (70.0, 977.8, 31.19),
    (80.0, 971.8, 47.39),
    (90.0, 965.3, 70.14),
    (100.0, 958.4, 101.325),
]

_DIESEL_TABLE: list[tuple[float, float, float]] = [
    (0.0, 860.0, 0.01),
    (20.0, 845.0, 0.05),
    (40.0, 830.0, 0.15),
    (60.0, 815.0, 0.40),
    (80.0, 800.0, 1.00),
    (100.0, 785.0, 2.50),
]

_SEAWATER_TABLE: list[tuple[float, float, float]] = [
    (5.0, 1027.7, 0.860),
    (10.0, 1026.9, 1.210),
    (15.0, 1025.9, 1.680),
    (20.0, 1024.7, 2.300),
    (25.0, 1023.3, 3.120),
    (30.0, 1021.7, 4.180),
    (40.0, 1017.9, 7.280),
    (50.0, 1013.5, 12.17),
    (60.0, 1008.4, 19.65),
    (80.0, 996.7, 46.70),
    (100.0, 983.2, 99.90),
]

_FLUID_TABLES: dict[str, list[tuple[float, float, float]]] = {
    "water": _WATER_TABLE,
    "diesel": _DIESEL_TABLE,
    "seawater": _SEAWATER_TABLE,
}

AVAILABLE_FLUIDS = list(_FLUID_TABLES.keys())


def _interpolate(table: list[tuple[float, float, float]], temp_c: float) -> tuple[float, float]:
    """Linear interpolation on a (temp, density, vapor_pressure) table."""
    if temp_c <= table[0][0]:
        return table[0][1], table[0][2]
    if temp_c >= table[-1][0]:
        return table[-1][1], table[-1][2]

    for i in range(len(table) - 1):
        t0, d0, vp0 = table[i]
        t1, d1, vp1 = table[i + 1]
        if t0 <= temp_c <= t1:
            frac = (temp_c - t0) / (t1 - t0)
            density = d0 + frac * (d1 - d0)
            vp = vp0 + frac * (vp1 - vp0)
            return round(density, 1), round(vp, 3)

    return table[-1][1], table[-1][2]


def get_fluid_properties(fluid: str, temp_c: float) -> FluidProperties:
    if fluid not in _FLUID_TABLES:
        raise ValueError(f"Unknown fluid '{fluid}'. Available: {AVAILABLE_FLUIDS}")

    density, vapor_pressure = _interpolate(_FLUID_TABLES[fluid], temp_c)
    return FluidProperties(
        fluid=fluid,
        temp_c=temp_c,
        density_kg_m3=density,
        vapor_pressure_kpa=vapor_pressure,
    )
