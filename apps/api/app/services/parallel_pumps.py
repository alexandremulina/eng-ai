from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.optimize import brentq


@dataclass
class PumpCurvePoint:
    q: float  # flow (m³/h)
    h: float  # head (m)


@dataclass
class SystemCurve:
    static_head: float  # H_static (m)
    resistance: float   # R coefficient — H_sys = static_head + R * Q^2


@dataclass
class PumpInput:
    name: str
    points: list[PumpCurvePoint]
    bep_q: float | None = None  # Best Efficiency Point flow (m³/h)


PumpAlert = Literal["off_curve", "reverse_flow"] | None


@dataclass
class PumpOperatingPoint:
    name: str
    q: float        # individual pump flow at operating H (m³/h)
    h: float        # operating head (m) — same for all pumps in parallel
    bep_ratio: float | None  # q / bep_q
    alert: PumpAlert


@dataclass
class OperatingPoint:
    q_total: float  # total combined flow (m³/h)
    h: float        # operating head (m)


@dataclass
class ChartPoint:
    q: float
    h: float


@dataclass
class ParallelPumpsResult:
    operating_point: OperatingPoint
    pumps: list[PumpOperatingPoint]
    combined_curve_points: list[ChartPoint]
    system_curve_points: list[ChartPoint]
    individual_curve_points: list[list[ChartPoint]]  # one list per pump


def _build_q_of_h(points: list[PumpCurvePoint]):
    """Return Q(H) function for a pump using cubic spline on H->Q (inverted)."""
    qs = np.array([p.q for p in points], dtype=float)
    hs = np.array([p.h for p in points], dtype=float)
    idx = np.argsort(qs)
    qs_sorted = qs[idx]
    hs_sorted = hs[idx]
    hq_spline = CubicSpline(qs_sorted, hs_sorted)
    h_min = float(hs_sorted.min())
    h_max = float(hs_sorted.max())
    q_min = float(qs_sorted.min())
    q_max = float(qs_sorted.max())

    def q_of_h(h: float) -> float:
        if h > h_max:
            return 0.0
        if h < h_min:
            return q_max
        try:
            return float(brentq(lambda q: hq_spline(q) - h, q_min, q_max))
        except ValueError:
            return 0.0

    return q_of_h, h_max, hq_spline, q_min, q_max


def calculate_parallel_pumps(
    pumps: list[PumpInput],
    system: SystemCurve,
    n_chart_points: int = 50,
) -> ParallelPumpsResult:
    if len(pumps) < 1:
        raise ValueError("At least one pump required")
    for pump in pumps:
        name = pump.name
        if len(pump.points) < 3:
            raise ValueError(f"Pump '{name}' needs at least 3 H-Q points")
        qs_check = [p.q for p in pump.points]
        if any(q < 0 for q in qs_check):
            raise ValueError(f"Pump '{name}' Q values must be non-negative")
        qs_sorted_check = sorted(qs_check)
        if len(qs_sorted_check) != len(set(qs_sorted_check)):
            raise ValueError(f"Pump '{name}' has duplicate Q values")
        # Validate strictly monotonically decreasing H as Q increases
        sorted_points = sorted(pump.points, key=lambda p: p.q)
        hs_check = [p.h for p in sorted_points]
        if not all(hs_check[i] > hs_check[i + 1] for i in range(len(hs_check) - 1)):
            raise ValueError(
                f"Pump '{name}' H-Q curve must be strictly monotonically decreasing"
            )

    pump_funcs = []
    for pump in pumps:
        q_of_h, h_max, hq_spline, q_min, q_max = _build_q_of_h(pump.points)
        pump_funcs.append((pump, q_of_h, h_max, hq_spline, q_min, q_max))

    h_op_max = max(pf[2] for pf in pump_funcs)  # combined curve extends to strongest pump shutoff
    h_op_min = system.static_head

    if h_op_min >= h_op_max:
        raise ValueError(
            "no_intersection: system static head exceeds all pump shutoff heads"
        )

    def q_total_of_h(h: float) -> float:
        return sum(pf[1](h) for pf in pump_funcs)

    def f(h: float) -> float:
        q = q_total_of_h(h)
        return h - system.static_head - system.resistance * q**2

    f_lo = f(h_op_min + 1e-6)
    f_hi = f(h_op_max - 1e-6)
    if f_lo * f_hi > 0:
        raise ValueError(
            "no_intersection: system curve does not bracket the combined pump curve"
        )
    try:
        h_op = float(brentq(f, h_op_min + 1e-6, h_op_max - 1e-6))
    except ValueError:
        raise ValueError(
            "no_intersection: system curve does not intersect combined pump curve"
        )

    q_op_total = q_total_of_h(h_op)

    pump_ops = []
    for pump, q_of_h, h_max, hq_spline, q_min, q_max in pump_funcs:
        q_i = q_of_h(h_op)
        bep_ratio = (q_i / pump.bep_q) if (pump.bep_q and pump.bep_q > 0) else None
        alert: PumpAlert = None
        if q_i < 0:
            alert = "reverse_flow"
        elif bep_ratio is not None and (bep_ratio < 0.8 or bep_ratio > 1.2):
            alert = "off_curve"
        pump_ops.append(PumpOperatingPoint(
            name=pump.name,
            q=round(q_i, 3),
            h=round(h_op, 3),
            bep_ratio=round(bep_ratio, 3) if bep_ratio is not None else None,
            alert=alert,
        ))

    h_range = np.linspace(h_op_min, h_op_max, n_chart_points)
    combined_curve = [
        ChartPoint(q=round(q_total_of_h(h), 3), h=round(h, 3))
        for h in h_range
    ]

    q_sys_range = np.linspace(0, q_op_total * 1.5, n_chart_points)
    system_curve = [
        ChartPoint(
            q=round(float(q), 3),
            h=round(system.static_head + system.resistance * q**2, 3),
        )
        for q in q_sys_range
    ]

    individual_curves = []
    for pump, q_of_h, h_max, hq_spline, q_min, q_max in pump_funcs:
        q_range = np.linspace(q_min, q_max, n_chart_points)
        curve = [
            ChartPoint(q=round(float(q), 3), h=round(float(hq_spline(q)), 3))
            for q in q_range
        ]
        individual_curves.append(curve)

    return ParallelPumpsResult(
        operating_point=OperatingPoint(
            q_total=round(q_op_total, 3),
            h=round(h_op, 3),
        ),
        pumps=pump_ops,
        combined_curve_points=combined_curve,
        system_curve_points=system_curve,
        individual_curve_points=individual_curves,
    )
