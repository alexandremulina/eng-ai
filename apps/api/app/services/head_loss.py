from __future__ import annotations

import math
from dataclasses import dataclass

import fluids


@dataclass
class HeadLossResult:
    head_loss_m: float
    velocity_m_s: float
    reynolds_number: float
    friction_factor: float
    flow_regime: str   # "laminar" | "turbulent" | "transitional"
    formula: str


def calculate_head_loss(
    flow_m3h: float,
    pipe_diameter_mm: float,
    pipe_length_m: float,
    pipe_roughness_mm: float,
    fluid_density_kg_m3: float,
    fluid_viscosity_cP: float,
) -> HeadLossResult:
    """
    Darcy-Weisbach: h_f = f * (L/D) * (v²/2g)

    Friction factor via Colebrook-White (fluids library).
    Laminar (Re < 2300): f = 64 / Re
    Turbulent/transitional (Re >= 2300): Colebrook-White via fluids
    """
    if flow_m3h <= 0:
        raise ValueError("flow_m3h must be positive")
    if pipe_diameter_mm <= 0:
        raise ValueError("pipe_diameter_mm must be positive")
    if pipe_length_m <= 0:
        raise ValueError("pipe_length_m must be positive")
    if fluid_density_kg_m3 <= 0:
        raise ValueError("fluid_density_kg_m3 must be positive")
    if fluid_viscosity_cP <= 0:
        raise ValueError("fluid_viscosity_cP must be positive")

    D = pipe_diameter_mm / 1000.0         # m
    roughness = pipe_roughness_mm / 1000.0  # m
    Q = flow_m3h / 3600.0                 # m³/s
    A = math.pi * (D / 2) ** 2            # m²
    v = Q / A                              # m/s
    mu = fluid_viscosity_cP * 1e-3        # Pa·s (dynamic viscosity)
    nu = mu / fluid_density_kg_m3         # m²/s (kinematic viscosity)

    Re = fluids.Reynolds(V=v, D=D, nu=nu)

    if Re < 2300:
        regime = "laminar"
        f = 64.0 / Re
    elif Re > 4000:
        regime = "turbulent"
        f = fluids.friction_factor(Re=Re, eD=roughness / D)
    else:
        regime = "transitional"
        f = fluids.friction_factor(Re=Re, eD=roughness / D)

    g = 9.81
    h_f = f * (pipe_length_m / D) * (v ** 2 / (2.0 * g))

    formula = (
        f"h_f = f × (L/D) × (v²/2g)\n"
        f"Re = {Re:.0f} ({regime}), f = {f:.6f}\n"
        f"v = {v:.4f} m/s\n"
        f"h_f = {f:.6f} × ({pipe_length_m}/{D:.3f}) × ({v:.4f}²/{2*g:.2f})\n"
        f"h_f = {round(h_f, 4)} m"
    )

    return HeadLossResult(
        head_loss_m=round(h_f, 4),
        velocity_m_s=round(v, 4),
        reynolds_number=round(Re, 1),
        friction_factor=round(f, 6),
        flow_regime=regime,
        formula=formula,
    )
