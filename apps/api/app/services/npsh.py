from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NPSHResult:
    npsha_m: float           # Available NPSH in meters
    npshr_m: float | None    # Required NPSH (if provided)
    safety_margin_m: float | None
    cavitation_risk: bool
    formula: str             # Human-readable formula used


def calculate_npsha(
    p_atm_kpa: float,
    p_vapor_kpa: float,
    z_s_m: float,
    h_loss_m: float,
    fluid_density_kg_m3: float,
    g: float = 9.81,
    npshr_m: float | None = None,
) -> NPSHResult:
    """
    NPSHa = (P_atm - P_vapor) / (rho * g) + Z_s - h_loss

    Args:
        p_atm_kpa: Absolute pressure at fluid surface (kPa)
        p_vapor_kpa: Fluid vapor pressure at operating temperature (kPa)
        z_s_m: Suction head (m) — positive if fluid above pump, negative if below
        h_loss_m: Total friction losses in suction piping (m)
        fluid_density_kg_m3: Fluid density (kg/m³)
        g: Gravitational acceleration (m/s²)
        npshr_m: Required NPSH from pump curve (m), optional
    """
    if fluid_density_kg_m3 <= 0:
        raise ValueError("fluid_density_kg_m3 must be positive")
    if g <= 0:
        raise ValueError("g must be positive")
    if h_loss_m < 0:
        raise ValueError("h_loss_m must be non-negative")

    pressure_head_m = ((p_atm_kpa - p_vapor_kpa) * 1000) / (fluid_density_kg_m3 * g)
    npsha_m = round(pressure_head_m + z_s_m - h_loss_m, 4)

    safety_margin: float | None = None
    cavitation_risk = False

    if npshr_m is not None:
        safety_margin = round(npsha_m - npshr_m, 4)
        cavitation_risk = npsha_m < npshr_m

    formula = (
        f"NPSHa = (P_atm - P_vapor) / (ρ·g) + Z_s - h_loss\n"
        f"     = ({p_atm_kpa} - {p_vapor_kpa}) kPa × 1000 / ({fluid_density_kg_m3} × {g}) + {z_s_m} - {h_loss_m}\n"
        f"     = {pressure_head_m:.4f} + {z_s_m} - {h_loss_m}\n"
        f"     = {npsha_m} m"
    )

    return NPSHResult(
        npsha_m=npsha_m,
        npshr_m=npshr_m,
        safety_margin_m=safety_margin,
        cavitation_risk=cavitation_risk,
        formula=formula,
    )
