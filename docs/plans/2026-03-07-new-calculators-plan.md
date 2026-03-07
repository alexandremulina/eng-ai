# New Calculators Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add 5 new engineering modules: parallel pump association (with AI curve extraction), material selection, galvanic corrosion checker, bolt torque, and ASME B16.5 flange dimensions.

**Architecture:** Each module follows the same pattern: pure Python service (dataclass result) → FastAPI router endpoint → Next.js form component + page. Frontend-only modules (galvanic, flanges) skip the API layer. Parallel pumps adds a second endpoint for AI-based curve extraction from uploaded files.

**Tech Stack:** Python scipy/numpy (backend math), FastAPI + Pydantic (API), OpenRouter Vision LLM (curve extraction), Next.js 15 + Recharts (frontend charts), TypeScript.

---

## Task 1: Parallel Pumps — Backend Service

**Files:**
- Create: `apps/api/app/services/parallel_pumps.py`
- Create: `apps/api/tests/test_parallel_pumps.py`

**Step 1: Write failing tests**

```python
# apps/api/tests/test_parallel_pumps.py
import pytest
from app.services.parallel_pumps import (
    PumpCurvePoint,
    SystemCurve,
    PumpInput,
    ParallelPumpsResult,
    calculate_parallel_pumps,
)


def test_single_pump_finds_operating_point():
    """Single pump on a system curve finds the correct operating point."""
    pump = PumpInput(
        name="Pump A",
        points=[
            PumpCurvePoint(q=0, h=50),
            PumpCurvePoint(q=10, h=45),
            PumpCurvePoint(q=20, h=35),
            PumpCurvePoint(q=30, h=20),
        ],
        bep_q=18.0,
    )
    system = SystemCurve(static_head=5.0, resistance=0.04)
    result = calculate_parallel_pumps(pumps=[pump], system=system)
    # H_sys = 5 + 0.04*Q^2, pump curve intersects around Q=20, H=21
    assert result.operating_point.h > 5
    assert result.operating_point.q_total > 0
    assert len(result.pumps) == 1
    assert result.pumps[0].q > 0


def test_two_identical_pumps_double_flow():
    """Two identical pumps in parallel should roughly double the flow vs single pump."""
    points = [
        PumpCurvePoint(q=0, h=50),
        PumpCurvePoint(q=10, h=45),
        PumpCurvePoint(q=20, h=35),
        PumpCurvePoint(q=30, h=20),
    ]
    pump_a = PumpInput(name="Pump A", points=points, bep_q=18.0)
    pump_b = PumpInput(name="Pump B", points=points, bep_q=18.0)
    system = SystemCurve(static_head=5.0, resistance=0.01)

    single = calculate_parallel_pumps(pumps=[pump_a], system=system)
    double = calculate_parallel_pumps(pumps=[pump_a, pump_b], system=system)

    # Two identical pumps should produce roughly 2x flow (not exactly due to system curve shape)
    assert double.operating_point.q_total > single.operating_point.q_total * 1.5


def test_dominated_pump_flagged_as_off_curve():
    """Pump with much lower head curve should be flagged as off_curve at operating point."""
    strong_pump = PumpInput(
        name="Strong",
        points=[
            PumpCurvePoint(q=0, h=60),
            PumpCurvePoint(q=15, h=50),
            PumpCurvePoint(q=30, h=35),
        ],
        bep_q=20.0,
    )
    weak_pump = PumpInput(
        name="Weak",
        points=[
            PumpCurvePoint(q=0, h=30),
            PumpCurvePoint(q=10, h=25),
            PumpCurvePoint(q=20, h=15),
        ],
        bep_q=10.0,
    )
    system = SystemCurve(static_head=20.0, resistance=0.05)
    result = calculate_parallel_pumps(pumps=[strong_pump, weak_pump], system=system)

    pump_results = {p.name: p for p in result.pumps}
    # At high system H, weak pump may operate far from BEP
    assert "Weak" in pump_results


def test_no_intersection_raises_value_error():
    """System curve above max pump head should raise ValueError."""
    pump = PumpInput(
        name="Pump A",
        points=[
            PumpCurvePoint(q=0, h=20),
            PumpCurvePoint(q=10, h=15),
            PumpCurvePoint(q=20, h=5),
        ],
        bep_q=10.0,
    )
    system = SystemCurve(static_head=50.0, resistance=0.01)  # way above pump max head
    with pytest.raises(ValueError, match="no_intersection"):
        calculate_parallel_pumps(pumps=[pump], system=system)


def test_combined_curve_points_returned():
    """Result includes combined curve points for charting."""
    points = [
        PumpCurvePoint(q=0, h=40),
        PumpCurvePoint(q=10, h=35),
        PumpCurvePoint(q=20, h=25),
        PumpCurvePoint(q=30, h=10),
    ]
    pump_a = PumpInput(name="A", points=points, bep_q=15.0)
    pump_b = PumpInput(name="B", points=points, bep_q=15.0)
    system = SystemCurve(static_head=5.0, resistance=0.02)
    result = calculate_parallel_pumps(pumps=[pump_a, pump_b], system=system)
    assert len(result.combined_curve_points) > 5
    assert len(result.system_curve_points) > 5
```

**Step 2: Run tests to verify they fail**

```bash
cd apps/api && python -m pytest tests/test_parallel_pumps.py -v
```

Expected: `ImportError` or `ModuleNotFoundError`

**Step 3: Implement the service**

```python
# apps/api/app/services/parallel_pumps.py
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
    # H must be strictly decreasing with Q for a valid pump curve
    # Sort by Q ascending, then invert: H->Q
    idx = np.argsort(qs)
    qs_sorted = qs[idx]
    hs_sorted = hs[idx]
    # Build H(Q) spline, then invert to Q(H) via root-finding
    hq_spline = CubicSpline(qs_sorted, hs_sorted)
    h_min = float(hs_sorted.min())
    h_max = float(hs_sorted.max())
    q_min = float(qs_sorted.min())
    q_max = float(qs_sorted.max())

    def q_of_h(h: float) -> float:
        if h > h_max:
            return 0.0  # pump cannot deliver this head
        if h < h_min:
            return q_max  # extrapolate to max flow
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
    """
    Solve parallel pump operating point.

    For parallel pumps, at any given H: Q_total = sum(Qi(H)) for each pump.
    The operating point is where Q_total(H) intersects H_sys(Q_total) = static_head + R*Q_total^2.
    """
    if len(pumps) < 1:
        raise ValueError("At least one pump required")
    for pump in pumps:
        if len(pump.points) < 3:
            raise ValueError(f"Pump '{pump.name}' needs at least 3 H-Q points")

    # Build Q(H) functions per pump
    pump_funcs = []
    for pump in pumps:
        q_of_h, h_max, hq_spline, q_min, q_max = _build_q_of_h(pump.points)
        pump_funcs.append((pump, q_of_h, h_max, hq_spline, q_min, q_max))

    # Combined H range: from static_head to min of all pump max heads
    h_op_max = min(pf[2] for pf in pump_funcs)
    h_op_min = system.static_head

    if h_op_min >= h_op_max:
        raise ValueError(
            "no_intersection: system static head exceeds all pump shutoff heads"
        )

    def q_total_of_h(h: float) -> float:
        return sum(pf[1](h) for pf in pump_funcs)

    # Find intersection: Q_total(H) = Q_sys(H) where H = static_head + R * Q_total^2
    # Rearrange: Q_total(H) - sqrt((H - static_head) / R) = 0
    # But better: define f(H) = H - static_head - R * Q_total(H)^2 = 0
    def f(h: float) -> float:
        q = q_total_of_h(h)
        return h - system.static_head - system.resistance * q**2

    try:
        h_op = float(brentq(f, h_op_min + 1e-6, h_op_max - 1e-6))
    except ValueError:
        raise ValueError(
            "no_intersection: system curve does not intersect combined pump curve"
        )

    q_op_total = q_total_of_h(h_op)

    # Individual pump operating points
    pump_ops = []
    for pump, q_of_h, h_max, hq_spline, q_min, q_max in pump_funcs:
        q_i = q_of_h(h_op)
        alert: PumpAlert = None
        if q_i < 0:
            alert = "reverse_flow"
        elif pump.bep_q is not None and pump.bep_q > 0:
            ratio = q_i / pump.bep_q
            if ratio < 0.8 or ratio > 1.2:
                alert = "off_curve"
        bep_ratio = (q_i / pump.bep_q) if pump.bep_q else None
        pump_ops.append(PumpOperatingPoint(
            name=pump.name,
            q=round(q_i, 3),
            h=round(h_op, 3),
            bep_ratio=round(bep_ratio, 3) if bep_ratio is not None else None,
            alert=alert,
        ))

    # Chart points: combined curve
    h_range = np.linspace(h_op_min, h_op_max, n_chart_points)
    combined_curve = [
        ChartPoint(q=round(q_total_of_h(h), 3), h=round(h, 3))
        for h in h_range
    ]

    # Chart points: system curve (Q from 0 to q_op_total * 1.5)
    q_sys_range = np.linspace(0, q_op_total * 1.5, n_chart_points)
    system_curve = [
        ChartPoint(
            q=round(float(q), 3),
            h=round(system.static_head + system.resistance * q**2, 3),
        )
        for q in q_sys_range
    ]

    # Chart points: individual pump curves
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
```

**Step 4: Run tests**

```bash
cd apps/api && python -m pytest tests/test_parallel_pumps.py -v
```

Expected: all 5 tests PASS

**Step 5: Commit**

```bash
git add apps/api/app/services/parallel_pumps.py apps/api/tests/test_parallel_pumps.py
git commit -m "feat: add parallel pump association service with scipy interpolation"
```

---

## Task 2: Parallel Pumps — API Endpoint

**Files:**
- Modify: `apps/api/app/routers/calculations.py`
- Modify: `apps/api/app/main.py` (add extract-curve endpoint if not there)
- Create: `apps/api/tests/test_parallel_pumps_endpoint.py`

**Step 1: Write failing endpoint tests**

```python
# apps/api/tests/test_parallel_pumps_endpoint.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

PUMP_A_POINTS = [
    {"q": 0, "h": 50}, {"q": 10, "h": 45},
    {"q": 20, "h": 35}, {"q": 30, "h": 20},
]
PUMP_B_POINTS = [
    {"q": 0, "h": 40}, {"q": 8, "h": 35},
    {"q": 16, "h": 25}, {"q": 24, "h": 10},
]


@pytest.mark.asyncio
async def test_parallel_pumps_two_pumps(mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/parallel-pumps", json={
            "pumps": [
                {"name": "Pump A", "points": PUMP_A_POINTS, "bep_q": 18.0},
                {"name": "Pump B", "points": PUMP_B_POINTS, "bep_q": 12.0},
            ],
            "system_curve": {"static_head": 5.0, "resistance": 0.04},
        })
    assert response.status_code == 200
    data = response.json()
    assert "operating_point" in data
    assert data["operating_point"]["q_total"] > 0
    assert data["operating_point"]["h"] > 5
    assert len(data["pumps"]) == 2
    assert len(data["combined_curve_points"]) > 5
    assert len(data["system_curve_points"]) > 5


@pytest.mark.asyncio
async def test_parallel_pumps_no_intersection_returns_400(mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/parallel-pumps", json={
            "pumps": [
                {"name": "Weak", "points": [
                    {"q": 0, "h": 10}, {"q": 5, "h": 7}, {"q": 10, "h": 2},
                ], "bep_q": 5.0},
            ],
            "system_curve": {"static_head": 50.0, "resistance": 0.01},
        })
    assert response.status_code == 400
    assert "no_intersection" in response.json()["detail"]


@pytest.mark.asyncio
async def test_parallel_pumps_too_few_points_returns_400(mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/parallel-pumps", json={
            "pumps": [
                {"name": "A", "points": [{"q": 0, "h": 50}], "bep_q": 10.0},
            ],
            "system_curve": {"static_head": 5.0, "resistance": 0.04},
        })
    assert response.status_code == 400
```

**Step 2: Run tests to verify they fail**

```bash
cd apps/api && python -m pytest tests/test_parallel_pumps_endpoint.py -v
```

Expected: FAIL (404 — route doesn't exist yet)

**Step 3: Add endpoint to calculations router**

Append to `apps/api/app/routers/calculations.py`:

```python
from app.services.parallel_pumps import (
    calculate_parallel_pumps,
    PumpCurvePoint as SvcPumpCurvePoint,
    SystemCurve as SvcSystemCurve,
    PumpInput as SvcPumpInput,
)


class PumpCurvePointModel(BaseModel):
    q: float = Field(..., ge=0, description="Flow rate (m³/h)")
    h: float = Field(..., ge=0, description="Head (m)")


class PumpInputModel(BaseModel):
    name: str
    points: list[PumpCurvePointModel] = Field(..., min_length=3)
    bep_q: float | None = Field(default=None, gt=0)


class SystemCurveModel(BaseModel):
    static_head: float = Field(..., ge=0, description="Static head (m)")
    resistance: float = Field(..., ge=0, description="System resistance coefficient R (H = H_static + R*Q²)")


class ParallelPumpsRequest(BaseModel):
    pumps: list[PumpInputModel] = Field(..., min_length=1, max_length=4)
    system_curve: SystemCurveModel


@router.post("/parallel-pumps")
async def parallel_pumps(req: ParallelPumpsRequest, user: dict = Depends(get_current_user)):
    try:
        check_and_record_usage(user["id"], "calculation")
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))
    try:
        result = calculate_parallel_pumps(
            pumps=[
                SvcPumpInput(
                    name=p.name,
                    points=[SvcPumpCurvePoint(q=pt.q, h=pt.h) for pt in p.points],
                    bep_q=p.bep_q,
                )
                for p in req.pumps
            ],
            system=SvcSystemCurve(
                static_head=req.system_curve.static_head,
                resistance=req.system_curve.resistance,
            ),
        )
        return {
            "operating_point": {
                "q_total": result.operating_point.q_total,
                "h": result.operating_point.h,
                "unit_q": "m3/h",
                "unit_h": "m",
            },
            "pumps": [
                {
                    "name": p.name,
                    "q": p.q,
                    "h": p.h,
                    "bep_ratio": p.bep_ratio,
                    "alert": p.alert,
                }
                for p in result.pumps
            ],
            "combined_curve_points": [{"q": pt.q, "h": pt.h} for pt in result.combined_curve_points],
            "system_curve_points": [{"q": pt.q, "h": pt.h} for pt in result.system_curve_points],
            "individual_curve_points": [
                [{"q": pt.q, "h": pt.h} for pt in curve]
                for curve in result.individual_curve_points
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Step 4: Run tests**

```bash
cd apps/api && python -m pytest tests/test_parallel_pumps_endpoint.py -v
```

Expected: all 3 PASS

**Step 5: Commit**

```bash
git add apps/api/app/routers/calculations.py apps/api/tests/test_parallel_pumps_endpoint.py
git commit -m "feat: add POST /calculations/parallel-pumps endpoint"
```

---

## Task 3: Parallel Pumps — Curve Extraction Endpoint

**Files:**
- Modify: `apps/api/app/routers/calculations.py`
- Create: `apps/api/tests/test_curve_extraction.py`

**Step 1: Write failing test**

```python
# apps/api/tests/test_curve_extraction.py
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_extract_curve_returns_points(mock_user):
    """Mock vision LLM returns valid H-Q points from an uploaded image."""
    fake_llm_response = '[{"q": 0, "h": 50}, {"q": 10, "h": 42}, {"q": 20, "h": 30}, {"q": 30, "h": 12}]'

    with patch("app.routers.calculations.call_vision_llm", new_callable=AsyncMock, return_value=fake_llm_response):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/calculations/extract-pump-curve",
                files={"file": ("curve.png", b"fake-image-bytes", "image/png")},
                headers={"Authorization": "Bearer test-token"},
            )
    assert response.status_code == 200
    data = response.json()
    assert "points" in data
    assert len(data["points"]) == 4
    assert data["points"][0]["q"] == 0
    assert data["points"][0]["h"] == 50


@pytest.mark.asyncio
async def test_extract_curve_invalid_llm_response_returns_400(mock_user):
    """If LLM returns garbage, endpoint returns 400."""
    with patch("app.routers.calculations.call_vision_llm", new_callable=AsyncMock, return_value="not valid json"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/calculations/extract-pump-curve",
                files={"file": ("curve.png", b"fake-image-bytes", "image/png")},
                headers={"Authorization": "Bearer test-token"},
            )
    assert response.status_code == 400
```

**Step 2: Run tests to verify they fail**

```bash
cd apps/api && python -m pytest tests/test_curve_extraction.py -v
```

Expected: FAIL (404)

**Step 3: Add extraction endpoint**

First check how `call_vision_llm` is imported in `apps/api/app/services/diagnosis.py`, then add to `calculations.py`:

```python
import base64
import json
from fastapi import UploadFile, File
from app.services.ai import call_vision_llm

CURVE_EXTRACTION_PROMPT = """
You are analyzing a pump performance curve chart.
Extract the H-Q (Head vs Flow) curve data points from this image.
Return ONLY a valid JSON array of objects with "q" (flow, numeric) and "h" (head, numeric) keys.
Extract at least 4 points spanning the full curve range.
Example: [{"q": 0, "h": 45}, {"q": 10, "h": 40}, {"q": 20, "h": 30}, {"q": 30, "h": 15}]
Do not include units, labels, or any text outside the JSON array.
"""


@router.post("/extract-pump-curve")
async def extract_pump_curve(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    content = await file.read()
    # Convert to base64 for vision LLM
    b64 = base64.b64encode(content).decode()
    mime = file.content_type or "image/png"

    try:
        raw = await call_vision_llm(
            prompt=CURVE_EXTRACTION_PROMPT,
            image_b64=b64,
            mime_type=mime,
        )
        # Strip markdown code fences if present
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        points = json.loads(raw)
        if not isinstance(points, list) or len(points) < 3:
            raise ValueError("Too few points extracted")
        # Validate structure
        validated = [{"q": float(p["q"]), "h": float(p["h"])} for p in points]
        return {"points": validated}
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Could not extract curve: {e}")
```

**Step 4: Run tests**

```bash
cd apps/api && python -m pytest tests/test_curve_extraction.py -v
```

Expected: both PASS

**Step 5: Commit**

```bash
git add apps/api/app/routers/calculations.py apps/api/tests/test_curve_extraction.py
git commit -m "feat: add POST /calculations/extract-pump-curve endpoint with vision LLM"
```

---

## Task 4: Bolt Torque — Backend Service

**Files:**
- Create: `apps/api/app/services/bolt_torque.py`
- Create: `apps/api/tests/test_bolt_torque.py`

**Step 1: Write failing tests**

```python
# apps/api/tests/test_bolt_torque.py
import pytest
from app.services.bolt_torque import calculate_bolt_torque, BoltTorqueResult

def test_b7_m20_dry():
    """ASTM A193 B7, M20 (20mm), dry condition."""
    result = calculate_bolt_torque(grade="ASTM A193 B7", diameter_mm=20.0, condition="dry")
    assert result.torque_nm > 0
    assert result.torque_ftlb > 0
    assert result.preload_kn > 0
    # B7 at M20 dry: ~300-400 N·m range
    assert 200 < result.torque_nm < 600

def test_iso_88_m16_lubricated():
    result = calculate_bolt_torque(grade="ISO 8.8", diameter_mm=16.0, condition="lubricated")
    assert result.torque_nm > 0
    # Lubricated should give less torque than dry for same bolt (K is lower)
    dry = calculate_bolt_torque(grade="ISO 8.8", diameter_mm=16.0, condition="dry")
    assert result.torque_nm < dry.torque_nm

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
```

**Step 2: Run tests**

```bash
cd apps/api && python -m pytest tests/test_bolt_torque.py -v
```

Expected: FAIL (`ImportError`)

**Step 3: Implement service**

```python
# apps/api/app/services/bolt_torque.py
from __future__ import annotations
import math
from dataclasses import dataclass

# Nut factor K per condition (dimensionless)
NUT_FACTOR = {
    "dry": 0.20,
    "lubricated": 0.15,
    "cadmium": 0.12,
}

# Grade → proof load (MPa), tensile strength (MPa)
# Sources: ASTM A193, ISO 898-1, SAE J429
GRADE_DATA: dict[str, dict] = {
    "ASTM A193 B7":  {"proof_mpa": 862,  "tensile_mpa": 1034},
    "ASTM A193 B8":  {"proof_mpa": 207,  "tensile_mpa": 517},
    "ISO 8.8":       {"proof_mpa": 600,  "tensile_mpa": 800},
    "ISO 10.9":      {"proof_mpa": 830,  "tensile_mpa": 1040},
    "ISO 12.9":      {"proof_mpa": 970,  "tensile_mpa": 1220},
    "SAE Grade 5":   {"proof_mpa": 585,  "tensile_mpa": 827},
    "SAE Grade 8":   {"proof_mpa": 827,  "tensile_mpa": 1034},
    "A2-70":         {"proof_mpa": 450,  "tensile_mpa": 700},
    "A4-80":         {"proof_mpa": 600,  "tensile_mpa": 800},
}

# Tensile stress area for standard metric threads (mm²) — ISO 898
# A_s = pi/4 * (d - 0.9382*p)^2  where p = pitch
# Pre-computed for common sizes
TENSILE_STRESS_AREA: dict[float, float] = {
    6.0:  20.1,
    8.0:  36.6,
    10.0: 58.0,
    12.0: 84.3,
    14.0: 115.0,
    16.0: 157.0,
    20.0: 245.0,
    24.0: 353.0,
    27.0: 459.0,
    30.0: 561.0,
    36.0: 817.0,
    42.0: 1120.0,
    48.0: 1470.0,
}


@dataclass
class BoltTorqueResult:
    grade: str
    diameter_mm: float
    condition: str
    proof_load_mpa: float
    preload_kn: float       # target preload force (kN)
    torque_nm: float        # tightening torque (N·m)
    torque_ftlb: float      # tightening torque (ft·lb)


def calculate_bolt_torque(
    grade: str,
    diameter_mm: float,
    condition: str = "dry",
) -> BoltTorqueResult:
    if grade not in GRADE_DATA:
        raise ValueError(f"Unknown grade '{grade}'. Available: {list(GRADE_DATA.keys())}")
    if condition not in NUT_FACTOR:
        raise ValueError(f"Unknown condition '{condition}'. Available: {list(NUT_FACTOR.keys())}")

    # Get closest standard size for stress area
    available = sorted(TENSILE_STRESS_AREA.keys())
    closest = min(available, key=lambda x: abs(x - diameter_mm))
    stress_area_mm2 = TENSILE_STRESS_AREA[closest]

    proof_mpa = GRADE_DATA[grade]["proof_mpa"]
    k = NUT_FACTOR[condition]
    d_m = diameter_mm / 1000  # convert mm to m

    # Target preload = 75% of proof load × stress area
    preload_n = 0.75 * proof_mpa * 1e6 * (stress_area_mm2 * 1e-6)  # N
    preload_kn = preload_n / 1000

    # Torque: T = K × Fi × d
    torque_nm = k * preload_n * d_m
    torque_ftlb = torque_nm * 0.737562  # N·m → ft·lb

    return BoltTorqueResult(
        grade=grade,
        diameter_mm=diameter_mm,
        condition=condition,
        proof_load_mpa=proof_mpa,
        preload_kn=round(preload_kn, 2),
        torque_nm=round(torque_nm, 1),
        torque_ftlb=round(torque_ftlb, 1),
    )
```

**Step 4: Run tests**

```bash
cd apps/api && python -m pytest tests/test_bolt_torque.py -v
```

Expected: all 4 PASS

**Step 5: Add endpoint to calculations router**

Append to `apps/api/app/routers/calculations.py`:

```python
from app.services.bolt_torque import calculate_bolt_torque


class BoltTorqueRequest(BaseModel):
    grade: str
    diameter_mm: float = Field(..., gt=0, le=100)
    condition: str = Field(default="dry")


@router.post("/bolt-torque")
async def bolt_torque(req: BoltTorqueRequest, user: dict = Depends(get_current_user)):
    try:
        result = calculate_bolt_torque(req.grade, req.diameter_mm, req.condition)
        return {
            "grade": result.grade,
            "diameter_mm": result.diameter_mm,
            "condition": result.condition,
            "proof_load_mpa": result.proof_load_mpa,
            "preload_kn": result.preload_kn,
            "torque_nm": result.torque_nm,
            "torque_ftlb": result.torque_ftlb,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Step 6: Commit**

```bash
git add apps/api/app/services/bolt_torque.py apps/api/app/routers/calculations.py apps/api/tests/test_bolt_torque.py
git commit -m "feat: add bolt torque service and POST /calculations/bolt-torque endpoint"
```

---

## Task 5: Material Selection — Backend Service

**Files:**
- Create: `apps/api/app/services/material_selection.py`
- Create: `apps/api/tests/test_material_selection.py`

**Step 1: Write failing tests**

```python
# apps/api/tests/test_material_selection.py
from app.services.material_selection import select_materials, MaterialRating

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
    assert "mechanical_seal" in components

def test_unknown_fluid_raises():
    from app.services.material_selection import select_materials
    import pytest
    with pytest.raises(ValueError, match="Unknown fluid"):
        select_materials(fluid="__unknown__", concentration_pct=50.0, temp_c=20.0)
```

**Step 2: Run tests**

```bash
cd apps/api && python -m pytest tests/test_material_selection.py -v
```

Expected: FAIL

**Step 3: Implement service**

```python
# apps/api/app/services/material_selection.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

Rating = Literal["recommended", "conditional", "incompatible"]


@dataclass
class MaterialRating:
    material: str
    rating: Rating
    note: str = ""


@dataclass
class ComponentRecommendation:
    component: str
    materials: list[MaterialRating]


# Compatibility table: fluid → component → material → (rating, note)
# Conditions: "recommended" = safe, "conditional" = check concentration/temp, "incompatible" = do not use
_TABLE: dict[str, dict[str, dict[str, tuple[Rating, str]]]] = {
    "water": {
        "casing":         {"Cast Iron": ("recommended", ""), "SS 316": ("recommended", ""), "Bronze": ("recommended", ""), "Duplex SS": ("recommended", "")},
        "impeller":       {"Cast Iron": ("recommended", ""), "SS 316": ("recommended", ""), "Bronze": ("recommended", ""), "Duplex SS": ("recommended", "")},
        "wear_ring":      {"Cast Iron": ("recommended", ""), "SS 316": ("recommended", ""), "Bronze": ("recommended", ""), "Duplex SS": ("recommended", "")},
        "shaft":          {"SS 316": ("recommended", ""), "Alloy 20": ("recommended", ""), "Carbon Steel": ("conditional", "use with coating")},
        "mechanical_seal":{"Carbon/SiC": ("recommended", ""), "Carbon/Ceramic": ("recommended", ""), "Viton": ("recommended", ""), "EPDM": ("recommended", "")},
    },
    "seawater": {
        "casing":         {"Cast Iron": ("conditional", "risk of corrosion without coating"), "SS 316": ("recommended", ""), "Bronze": ("recommended", ""), "Duplex SS": ("recommended", ""), "Super Duplex": ("recommended", "")},
        "impeller":       {"Cast Iron": ("incompatible", "galvanic corrosion risk"), "SS 316": ("conditional", "check chloride levels"), "Bronze": ("recommended", ""), "Duplex SS": ("recommended", ""), "Super Duplex": ("recommended", "")},
        "wear_ring":      {"SS 316": ("conditional", ""), "Bronze": ("recommended", ""), "Super Duplex": ("recommended", "")},
        "shaft":          {"SS 316": ("conditional", "pitting risk"), "Duplex SS": ("recommended", ""), "Super Duplex": ("recommended", "")},
        "mechanical_seal":{"SiC/SiC": ("recommended", ""), "Carbon/SiC": ("recommended", ""), "Viton": ("recommended", ""), "EPDM": ("incompatible", "")},
    },
    "sulfuric_acid": {
        "casing":         {"Cast Iron": ("incompatible", ""), "SS 316": ("conditional", "< 5% or > 93% concentration"), "Alloy 20": ("recommended", ""), "Hastelloy C": ("recommended", ""), "PTFE-lined": ("recommended", "")},
        "impeller":       {"Cast Iron": ("incompatible", ""), "SS 316": ("conditional", "narrow concentration range"), "Alloy 20": ("recommended", ""), "Hastelloy C": ("recommended", "")},
        "wear_ring":      {"SS 316": ("conditional", ""), "Alloy 20": ("recommended", ""), "Hastelloy C": ("recommended", "")},
        "shaft":          {"SS 316": ("conditional", ""), "Alloy 20": ("recommended", ""), "Hastelloy C": ("recommended", "")},
        "mechanical_seal":{"SiC/SiC": ("recommended", ""), "Carbon/SiC": ("conditional", "< 60% conc"), "PTFE": ("recommended", ""), "Viton": ("incompatible", "")},
    },
    "hydrochloric_acid": {
        "casing":         {"Cast Iron": ("incompatible", ""), "SS 316": ("incompatible", ""), "Hastelloy C": ("recommended", ""), "Rubber-lined": ("recommended", ""), "PTFE-lined": ("recommended", "")},
        "impeller":       {"Cast Iron": ("incompatible", ""), "SS 316": ("incompatible", ""), "Hastelloy C": ("recommended", ""), "Rubber": ("recommended", "< 60°C")},
        "wear_ring":      {"Hastelloy C": ("recommended", ""), "PTFE": ("recommended", "")},
        "shaft":          {"Hastelloy C": ("recommended", ""), "SS 316": ("incompatible", "")},
        "mechanical_seal":{"SiC/SiC": ("recommended", ""), "Carbon/SiC": ("incompatible", ""), "PTFE": ("recommended", ""), "Viton": ("incompatible", "")},
    },
    "caustic_soda": {
        "casing":         {"Cast Iron": ("recommended", ""), "SS 316": ("recommended", ""), "Carbon Steel": ("recommended", "< 60°C"), "Duplex SS": ("recommended", "")},
        "impeller":       {"Cast Iron": ("recommended", ""), "SS 316": ("recommended", ""), "Carbon Steel": ("conditional", ""), "Duplex SS": ("recommended", "")},
        "wear_ring":      {"Cast Iron": ("recommended", ""), "SS 316": ("recommended", "")},
        "shaft":          {"SS 316": ("recommended", ""), "Carbon Steel": ("conditional", "")},
        "mechanical_seal":{"Carbon/SiC": ("recommended", ""), "SiC/SiC": ("recommended", ""), "EPDM": ("recommended", ""), "Viton": ("incompatible", "")},
    },
    "diesel": {
        "casing":         {"Cast Iron": ("recommended", ""), "Carbon Steel": ("recommended", ""), "SS 316": ("recommended", ""), "Bronze": ("recommended", "")},
        "impeller":       {"Cast Iron": ("recommended", ""), "Carbon Steel": ("recommended", ""), "SS 316": ("recommended", ""), "Bronze": ("recommended", "")},
        "wear_ring":      {"Cast Iron": ("recommended", ""), "SS 316": ("recommended", ""), "Bronze": ("recommended", "")},
        "shaft":          {"Carbon Steel": ("recommended", ""), "SS 316": ("recommended", "")},
        "mechanical_seal":{"Carbon/SiC": ("recommended", ""), "Viton": ("recommended", ""), "NBR": ("recommended", ""), "EPDM": ("incompatible", "")},
    },
}

COMPONENTS = ["casing", "impeller", "wear_ring", "shaft", "mechanical_seal"]


def select_materials(
    fluid: str,
    concentration_pct: float,
    temp_c: float,
) -> list[ComponentRecommendation]:
    if fluid not in _TABLE:
        raise ValueError(f"Unknown fluid '{fluid}'. Available: {list(_TABLE.keys())}")

    fluid_data = _TABLE[fluid]
    result = []
    for component in COMPONENTS:
        if component not in fluid_data:
            continue
        comp_data = fluid_data[component]
        materials = [
            MaterialRating(material=mat, rating=rating, note=note)
            for mat, (rating, note) in comp_data.items()
        ]
        result.append(ComponentRecommendation(component=component, materials=materials))
    return result
```

**Step 4: Run tests**

```bash
cd apps/api && python -m pytest tests/test_material_selection.py -v
```

Expected: all PASS

**Step 5: Add endpoint**

Append to `apps/api/app/routers/calculations.py`:

```python
from app.services.material_selection import select_materials


class MaterialSelectionRequest(BaseModel):
    fluid: str
    concentration_pct: float = Field(default=100.0, ge=0, le=100)
    temp_c: float = Field(default=25.0)


@router.post("/material-selection")
async def material_selection(req: MaterialSelectionRequest, user: dict = Depends(get_current_user)):
    try:
        result = select_materials(req.fluid, req.concentration_pct, req.temp_c)
        return {
            "fluid": req.fluid,
            "components": [
                {
                    "component": c.component,
                    "materials": [
                        {"material": m.material, "rating": m.rating, "note": m.note}
                        for m in c.materials
                    ],
                }
                for c in result
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Step 6: Commit**

```bash
git add apps/api/app/services/material_selection.py apps/api/app/routers/calculations.py apps/api/tests/test_material_selection.py
git commit -m "feat: add material selection service and POST /calculations/material-selection endpoint"
```

---

## Task 6: Frontend — Add API Methods

**Files:**
- Modify: `apps/web/lib/api.ts`

**Step 1: Add new API methods**

```typescript
// Append to the `api` object in apps/web/lib/api.ts:

parallelPumps: (body: object, token: string) =>
  apiFetch("/calculations/parallel-pumps", { method: "POST", body: JSON.stringify(body), token }),

extractPumpCurve: (formData: FormData, token: string) =>
  apiFetch("/calculations/extract-pump-curve", {
    method: "POST",
    body: formData,
    token,
    headers: {},
  }),

boltTorque: (body: object, token: string) =>
  apiFetch("/calculations/bolt-torque", { method: "POST", body: JSON.stringify(body), token }),

materialSelection: (body: object, token: string) =>
  apiFetch("/calculations/material-selection", { method: "POST", body: JSON.stringify(body), token }),
```

**Step 2: Commit**

```bash
git add apps/web/lib/api.ts
git commit -m "feat: add parallelPumps, extractPumpCurve, boltTorque, materialSelection to api client"
```

---

## Task 7: Frontend — Galvanic Corrosion (pure frontend)

**Files:**
- Create: `apps/web/lib/galvanic.ts`
- Create: `apps/web/app/(app)/calc/galvanic/page.tsx`
- Create: `apps/web/components/calc/GalvanicForm.tsx`

**Step 1: Create galvanic data and logic**

```typescript
// apps/web/lib/galvanic.ts

// Galvanic potential in mV vs SCE (approximate, passive range midpoint)
// Source: NACE / MIL-STD-889C
export const GALVANIC_SERIES: Record<string, number> = {
  "Zinc":                  -1000,
  "Aluminum 1100":          -750,
  "Aluminum 6061":          -730,
  "Carbon Steel":           -620,
  "Cast Iron":              -610,
  "SS 304 (active)":        -530,
  "SS 316 (active)":        -500,
  "Lead-Tin Solder":        -480,
  "Lead":                   -460,
  "Tin":                    -440,
  "Muntz Metal":            -380,
  "Yellow Brass":           -360,
  "Admiralty Brass":        -330,
  "Aluminum Bronze":        -320,
  "Red Brass":              -310,
  "Bronze (92Cu-8Sn)":      -300,
  "Copper":                 -280,
  "Nickel Silver":          -270,
  "Cupronickel (70-30)":    -200,
  "Monel 400":              -150,
  "SS 316 (passive)":        -50,
  "SS 304 (passive)":        -80,
  "Titanium Grade 2":        -50,
  "Hastelloy C":             -30,
  "Platinum":                  0,
  "Graphite":                 +50,
}

export type GalvanicRisk = "low" | "medium" | "high"

export interface GalvanicResult {
  anode: string        // material that corrodes (more negative)
  cathode: string      // material protected
  potential_mv: number // absolute difference
  risk: GalvanicRisk
  recommendation: string
}

export function checkGalvanicCompatibility(mat1: string, mat2: string): GalvanicResult {
  const v1 = GALVANIC_SERIES[mat1]
  const v2 = GALVANIC_SERIES[mat2]
  if (v1 === undefined || v2 === undefined) {
    throw new Error("Unknown material")
  }
  const diff = Math.abs(v1 - v2)
  const anode = v1 < v2 ? mat1 : mat2
  const cathode = v1 < v2 ? mat2 : mat1

  let risk: GalvanicRisk
  let recommendation: string

  if (diff < 50) {
    risk = "low"
    recommendation = "Compatible — minimal galvanic corrosion risk."
  } else if (diff < 250) {
    risk = "medium"
    recommendation = `Moderate risk. ${anode} will corrode preferentially. Consider insulating gasket or coating.`
  } else {
    risk = "high"
    recommendation = `High risk. ${anode} will corrode rapidly. Isolate materials with non-conductive gasket, coating, or use intermediate alloy.`
  }

  return { anode, cathode, potential_mv: diff, risk, recommendation }
}
```

**Step 2: Create the page and form**

```tsx
// apps/web/components/calc/GalvanicForm.tsx
"use client"
import { useState } from "react"
import { GALVANIC_SERIES, checkGalvanicCompatibility, GalvanicResult } from "@/lib/galvanic"

const MATERIALS = Object.keys(GALVANIC_SERIES)

export function GalvanicForm() {
  const [mat1, setMat1] = useState("")
  const [mat2, setMat2] = useState("")
  const [result, setResult] = useState<GalvanicResult | null>(null)

  function check() {
    if (!mat1 || !mat2 || mat1 === mat2) return
    setResult(checkGalvanicCompatibility(mat1, mat2))
  }

  const riskColors = { low: "text-green-400", medium: "text-yellow-400", high: "text-red-400" }
  const riskBg = { low: "bg-green-900/30 border-green-500/30", medium: "bg-yellow-900/30 border-yellow-500/30", high: "bg-red-900/30 border-red-500/30" }

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        {[
          { label: "Material 1", value: mat1, set: setMat1 },
          { label: "Material 2", value: mat2, set: setMat2 },
        ].map(({ label, value, set }) => (
          <div key={label} className="space-y-1">
            <label className="block text-sm font-medium text-white/80">{label}</label>
            <select
              value={value}
              onChange={e => { set(e.target.value); setResult(null) }}
              className="w-full h-12 px-3 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:border-blue-500"
            >
              <option value="">Select material...</option>
              {MATERIALS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
        ))}
        <button
          onClick={check}
          disabled={!mat1 || !mat2 || mat1 === mat2}
          className="w-full h-12 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium transition-colors"
        >
          Check Compatibility
        </button>
      </div>

      {result && (
        <div className={`rounded-lg border p-4 space-y-3 ${riskBg[result.risk]}`}>
          <div className="flex items-center justify-between">
            <span className={`text-lg font-bold uppercase ${riskColors[result.risk]}`}>
              {result.risk} risk
            </span>
            <span className="text-white/60 text-sm">{result.potential_mv} mV difference</span>
          </div>
          <div className="text-sm text-white/70 space-y-1">
            <p>Anode (corrodes): <span className="text-red-400 font-medium">{result.anode}</span></p>
            <p>Cathode (protected): <span className="text-green-400 font-medium">{result.cathode}</span></p>
          </div>
          <p className="text-sm text-white/80">{result.recommendation}</p>
        </div>
      )}
    </div>
  )
}
```

```tsx
// apps/web/app/(app)/calc/galvanic/page.tsx
import { GalvanicForm } from "@/components/calc/GalvanicForm"
import Link from "next/link"
import { ChevronLeft } from "lucide-react"

export const metadata = { title: "Galvanic Corrosion — EngBrain" }

export default function GalvanicPage() {
  return (
    <div className="p-4">
      <Link href="/calc" className="flex items-center gap-1 text-sm text-white/50 hover:text-white/80 mb-4 transition-colors">
        <ChevronLeft size={16} /> Back to Calculators
      </Link>
      <h1 className="text-xl font-bold text-white mb-1">Galvanic Corrosion Check</h1>
      <p className="text-sm text-white/50 mb-6">Assess compatibility between two materials in contact</p>
      <GalvanicForm />
    </div>
  )
}
```

**Step 3: Commit**

```bash
git add apps/web/lib/galvanic.ts apps/web/components/calc/GalvanicForm.tsx apps/web/app/(app)/calc/galvanic/page.tsx
git commit -m "feat: add galvanic corrosion checker (frontend-only, galvanic series lookup)"
```

---

## Task 8: Frontend — ASME B16.5 Flanges (pure frontend)

**Files:**
- Create: `apps/web/lib/flanges.ts`
- Create: `apps/web/components/calc/FlangeTable.tsx`
- Create: `apps/web/app/(app)/calc/flanges/page.tsx`

**Step 1: Create flange data**

```typescript
// apps/web/lib/flanges.ts

export interface FlangeDimensions {
  nps: string
  class: number
  od_mm: number
  bolt_circle_mm: number
  num_bolts: number
  bolt_hole_mm: number
  thickness_mm: number
  rf_od_mm: number   // raised face OD
  rf_height_mm: number
}

// ASME B16.5 dimensional data (mm) — Class 150 and 300 for NPS ½" to 12"
// These are engineering reference values widely reproduced in textbooks and engineering handbooks.
export const FLANGE_DATA: FlangeDimensions[] = [
  // Class 150
  { nps: "1/2",  class: 150, od_mm: 89,  bolt_circle_mm: 60.3,  num_bolts: 4,  bolt_hole_mm: 15.9, thickness_mm: 11.2, rf_od_mm: 35,  rf_height_mm: 1.6 },
  { nps: "3/4",  class: 150, od_mm: 98,  bolt_circle_mm: 69.9,  num_bolts: 4,  bolt_hole_mm: 15.9, thickness_mm: 12.7, rf_od_mm: 43,  rf_height_mm: 1.6 },
  { nps: "1",    class: 150, od_mm: 108, bolt_circle_mm: 79.4,  num_bolts: 4,  bolt_hole_mm: 15.9, thickness_mm: 14.3, rf_od_mm: 51,  rf_height_mm: 1.6 },
  { nps: "1-1/2",class: 150, od_mm: 127, bolt_circle_mm: 98.4,  num_bolts: 4,  bolt_hole_mm: 15.9, thickness_mm: 17.5, rf_od_mm: 70,  rf_height_mm: 1.6 },
  { nps: "2",    class: 150, od_mm: 152, bolt_circle_mm: 120.7, num_bolts: 4,  bolt_hole_mm: 19.1, thickness_mm: 19.1, rf_od_mm: 92,  rf_height_mm: 1.6 },
  { nps: "3",    class: 150, od_mm: 191, bolt_circle_mm: 152.4, num_bolts: 4,  bolt_hole_mm: 19.1, thickness_mm: 23.9, rf_od_mm: 127, rf_height_mm: 1.6 },
  { nps: "4",    class: 150, od_mm: 229, bolt_circle_mm: 190.5, num_bolts: 8,  bolt_hole_mm: 19.1, thickness_mm: 23.9, rf_od_mm: 157, rf_height_mm: 1.6 },
  { nps: "6",    class: 150, od_mm: 279, bolt_circle_mm: 241.3, num_bolts: 8,  bolt_hole_mm: 22.4, thickness_mm: 25.4, rf_od_mm: 216, rf_height_mm: 1.6 },
  { nps: "8",    class: 150, od_mm: 343, bolt_circle_mm: 298.5, num_bolts: 8,  bolt_hole_mm: 22.4, thickness_mm: 28.6, rf_od_mm: 270, rf_height_mm: 1.6 },
  { nps: "10",   class: 150, od_mm: 406, bolt_circle_mm: 362.0, num_bolts: 12, bolt_hole_mm: 25.4, thickness_mm: 30.2, rf_od_mm: 324, rf_height_mm: 1.6 },
  { nps: "12",   class: 150, od_mm: 483, bolt_circle_mm: 431.8, num_bolts: 12, bolt_hole_mm: 25.4, thickness_mm: 31.8, rf_od_mm: 381, rf_height_mm: 1.6 },
  // Class 300
  { nps: "1/2",  class: 300, od_mm: 95,  bolt_circle_mm: 66.7,  num_bolts: 4,  bolt_hole_mm: 15.9, thickness_mm: 14.3, rf_od_mm: 35,  rf_height_mm: 1.6 },
  { nps: "3/4",  class: 300, od_mm: 117, bolt_circle_mm: 82.6,  num_bolts: 4,  bolt_hole_mm: 19.1, thickness_mm: 15.9, rf_od_mm: 43,  rf_height_mm: 1.6 },
  { nps: "1",    class: 300, od_mm: 124, bolt_circle_mm: 88.9,  num_bolts: 4,  bolt_hole_mm: 19.1, thickness_mm: 17.5, rf_od_mm: 51,  rf_height_mm: 1.6 },
  { nps: "1-1/2",class: 300, od_mm: 156, bolt_circle_mm: 114.3, num_bolts: 4,  bolt_hole_mm: 22.4, thickness_mm: 22.4, rf_od_mm: 70,  rf_height_mm: 1.6 },
  { nps: "2",    class: 300, od_mm: 165, bolt_circle_mm: 127.0, num_bolts: 8,  bolt_hole_mm: 19.1, thickness_mm: 25.4, rf_od_mm: 92,  rf_height_mm: 1.6 },
  { nps: "3",    class: 300, od_mm: 210, bolt_circle_mm: 168.3, num_bolts: 8,  bolt_hole_mm: 22.4, thickness_mm: 31.8, rf_od_mm: 127, rf_height_mm: 1.6 },
  { nps: "4",    class: 300, od_mm: 254, bolt_circle_mm: 200.0, num_bolts: 8,  bolt_hole_mm: 22.4, thickness_mm: 38.1, rf_od_mm: 157, rf_height_mm: 1.6 },
  { nps: "6",    class: 300, od_mm: 318, bolt_circle_mm: 269.9, num_bolts: 12, bolt_hole_mm: 22.4, thickness_mm: 44.5, rf_od_mm: 216, rf_height_mm: 1.6 },
  { nps: "8",    class: 300, od_mm: 381, bolt_circle_mm: 330.2, num_bolts: 12, bolt_hole_mm: 25.4, thickness_mm: 50.8, rf_od_mm: 270, rf_height_mm: 1.6 },
  { nps: "10",   class: 300, od_mm: 444, bolt_circle_mm: 387.4, num_bolts: 16, bolt_hole_mm: 28.6, thickness_mm: 57.2, rf_od_mm: 324, rf_height_mm: 1.6 },
  { nps: "12",   class: 300, od_mm: 521, bolt_circle_mm: 450.9, num_bolts: 16, bolt_hole_mm: 28.6, thickness_mm: 63.5, rf_od_mm: 381, rf_height_mm: 1.6 },
  // Class 600
  { nps: "1/2",  class: 600, od_mm: 95,  bolt_circle_mm: 66.7,  num_bolts: 4,  bolt_hole_mm: 15.9, thickness_mm: 22.4, rf_od_mm: 35,  rf_height_mm: 6.4 },
  { nps: "1",    class: 600, od_mm: 124, bolt_circle_mm: 88.9,  num_bolts: 4,  bolt_hole_mm: 19.1, thickness_mm: 25.4, rf_od_mm: 51,  rf_height_mm: 6.4 },
  { nps: "2",    class: 600, od_mm: 165, bolt_circle_mm: 127.0, num_bolts: 8,  bolt_hole_mm: 19.1, thickness_mm: 38.1, rf_od_mm: 92,  rf_height_mm: 6.4 },
  { nps: "4",    class: 600, od_mm: 273, bolt_circle_mm: 215.9, num_bolts: 8,  bolt_hole_mm: 25.4, thickness_mm: 54.0, rf_od_mm: 157, rf_height_mm: 6.4 },
  { nps: "6",    class: 600, od_mm: 356, bolt_circle_mm: 292.1, num_bolts: 12, bolt_hole_mm: 28.6, thickness_mm: 63.5, rf_od_mm: 216, rf_height_mm: 6.4 },
  { nps: "8",    class: 600, od_mm: 419, bolt_circle_mm: 349.2, num_bolts: 12, bolt_hole_mm: 31.8, thickness_mm: 76.2, rf_od_mm: 270, rf_height_mm: 6.4 },
  { nps: "10",   class: 600, od_mm: 508, bolt_circle_mm: 431.8, num_bolts: 16, bolt_hole_mm: 34.9, thickness_mm: 88.9, rf_od_mm: 324, rf_height_mm: 6.4 },
  { nps: "12",   class: 600, od_mm: 559, bolt_circle_mm: 489.0, num_bolts: 20, bolt_hole_mm: 34.9, thickness_mm: 101.6, rf_od_mm: 381, rf_height_mm: 6.4 },
]

export const NPS_OPTIONS = [...new Set(FLANGE_DATA.map(f => f.nps))]
export const CLASS_OPTIONS = [...new Set(FLANGE_DATA.map(f => f.class))].sort((a, b) => a - b)

export function getFlangeDimensions(nps: string, cls: number): FlangeDimensions | null {
  return FLANGE_DATA.find(f => f.nps === nps && f.class === cls) ?? null
}
```

**Step 2: Create page and component**

```tsx
// apps/web/components/calc/FlangeTable.tsx
"use client"
import { useState } from "react"
import { NPS_OPTIONS, CLASS_OPTIONS, getFlangeDimensions, FlangeDimensions } from "@/lib/flanges"

export function FlangeTable() {
  const [nps, setNps] = useState("")
  const [cls, setCls] = useState<number | "">("")
  const dims: FlangeDimensions | null = nps && cls ? getFlangeDimensions(nps, Number(cls)) : null

  const rows: [string, string][] = dims ? [
    ["Flange OD", `${dims.od_mm} mm`],
    ["Bolt Circle Diameter", `${dims.bolt_circle_mm} mm`],
    ["Number of Bolts", `${dims.num_bolts}`],
    ["Bolt Hole Diameter", `${dims.bolt_hole_mm} mm`],
    ["Flange Thickness (min)", `${dims.thickness_mm} mm`],
    ["Raised Face OD", `${dims.rf_od_mm} mm`],
    ["Raised Face Height", `${dims.rf_height_mm} mm`],
  ] : []

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <label className="block text-sm font-medium text-white/80">NPS</label>
          <select
            value={nps}
            onChange={e => setNps(e.target.value)}
            className="w-full h-12 px-3 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:border-blue-500"
          >
            <option value="">Select NPS</option>
            {NPS_OPTIONS.map(n => <option key={n} value={n}>{n}"</option>)}
          </select>
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-white/80">Pressure Class</label>
          <select
            value={cls}
            onChange={e => setCls(Number(e.target.value))}
            className="w-full h-12 px-3 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:border-blue-500"
          >
            <option value="">Select class</option>
            {CLASS_OPTIONS.map(c => <option key={c} value={c}>{c}#</option>)}
          </select>
        </div>
      </div>

      {dims && (
        <div className="rounded-lg border border-white/10 overflow-hidden" style={{ backgroundColor: "#1A1D27" }}>
          <div className="p-3 border-b border-white/10">
            <h3 className="text-sm font-semibold text-white">NPS {dims.nps}" — Class {dims.class}# (ASME B16.5)</h3>
          </div>
          <table className="w-full text-sm">
            <tbody>
              {rows.map(([label, value]) => (
                <tr key={label} className="border-b border-white/5 last:border-0">
                  <td className="p-3 text-white/50">{label}</td>
                  <td className="p-3 text-white font-medium text-right">{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {nps && cls && !dims && (
        <p className="text-sm text-yellow-400">No data available for NPS {nps}" Class {cls}#.</p>
      )}
    </div>
  )
}
```

```tsx
// apps/web/app/(app)/calc/flanges/page.tsx
import { FlangeTable } from "@/components/calc/FlangeTable"
import Link from "next/link"
import { ChevronLeft } from "lucide-react"

export const metadata = { title: "ASME B16.5 Flanges — EngBrain" }

export default function FlangesPage() {
  return (
    <div className="p-4">
      <Link href="/calc" className="flex items-center gap-1 text-sm text-white/50 hover:text-white/80 mb-4 transition-colors">
        <ChevronLeft size={16} /> Back to Calculators
      </Link>
      <h1 className="text-xl font-bold text-white mb-1">ASME B16.5 Flanges</h1>
      <p className="text-sm text-white/50 mb-6">Flange dimensions by NPS and pressure class</p>
      <FlangeTable />
    </div>
  )
}
```

**Step 3: Commit**

```bash
git add apps/web/lib/flanges.ts apps/web/components/calc/FlangeTable.tsx apps/web/app/(app)/calc/flanges/page.tsx
git commit -m "feat: add ASME B16.5 flange dimension lookup (frontend-only)"
```

---

## Task 9: Frontend — Bolt Torque UI

**Files:**
- Create: `apps/web/components/calc/BoltTorqueForm.tsx`
- Create: `apps/web/app/(app)/calc/bolt-torque/page.tsx`

**Step 1: Create the form**

```tsx
// apps/web/components/calc/BoltTorqueForm.tsx
"use client"
import { useState } from "react"
import { toast } from "sonner"
import { api, ApiError } from "@/lib/api"
import { useSession } from "@/lib/useSession"

const GRADES = ["ASTM A193 B7", "ASTM A193 B8", "ISO 8.8", "ISO 10.9", "ISO 12.9", "SAE Grade 5", "SAE Grade 8", "A2-70", "A4-80"]
const DIAMETERS = [6, 8, 10, 12, 14, 16, 20, 24, 27, 30, 36, 42, 48]
const CONDITIONS = [{ value: "dry", label: "Dry" }, { value: "lubricated", label: "Lubricated (oil/grease)" }, { value: "cadmium", label: "Cadmium-plated" }]

interface BoltResult {
  grade: string
  diameter_mm: number
  condition: string
  proof_load_mpa: number
  preload_kn: number
  torque_nm: number
  torque_ftlb: number
}

export function BoltTorqueForm() {
  const { token } = useSession()
  const [grade, setGrade] = useState(GRADES[0])
  const [diameter, setDiameter] = useState(20)
  const [condition, setCondition] = useState("dry")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<BoltResult | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!token) { toast.error("Please log in"); return }
    setLoading(true)
    try {
      const data = await api.boltTorque({ grade, diameter_mm: diameter, condition }, token) as BoltResult
      setResult(data)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Calculation failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-1">
          <label className="block text-sm font-medium text-white/80">Bolt Grade</label>
          <select value={grade} onChange={e => setGrade(e.target.value)} className="w-full h-12 px-3 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:border-blue-500">
            {GRADES.map(g => <option key={g} value={g}>{g}</option>)}
          </select>
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-white/80">Nominal Diameter (mm)</label>
          <select value={diameter} onChange={e => setDiameter(Number(e.target.value))} className="w-full h-12 px-3 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:border-blue-500">
            {DIAMETERS.map(d => <option key={d} value={d}>M{d}</option>)}
          </select>
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-white/80">Condition</label>
          {CONDITIONS.map(c => (
            <label key={c.value} className="flex items-center gap-3 p-3 rounded-lg border border-white/10 cursor-pointer hover:border-blue-500/50 transition-colors">
              <input type="radio" name="condition" value={c.value} checked={condition === c.value} onChange={() => setCondition(c.value)} className="accent-blue-500" />
              <span className="text-white/80 text-sm">{c.label}</span>
            </label>
          ))}
        </div>
        <button type="submit" disabled={loading} className="w-full h-12 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium transition-colors">
          {loading ? "Calculating..." : "Calculate Torque"}
        </button>
      </form>

      {result && (
        <div className="rounded-lg border border-white/10 p-4 space-y-3" style={{ backgroundColor: "#1A1D27" }}>
          <h3 className="text-base font-semibold text-white">Result — {result.grade} M{result.diameter_mm} ({result.condition})</h3>
          <div className="text-4xl font-bold text-blue-400">{result.torque_nm} N·m</div>
          <p className="text-sm text-white/50">{result.torque_ftlb} ft·lb</p>
          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-white/10 text-sm">
            <div>
              <p className="text-white/40">Preload Force</p>
              <p className="text-white font-medium">{result.preload_kn} kN</p>
            </div>
            <div>
              <p className="text-white/40">Proof Load</p>
              <p className="text-white font-medium">{result.proof_load_mpa} MPa</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
```

```tsx
// apps/web/app/(app)/calc/bolt-torque/page.tsx
import { BoltTorqueForm } from "@/components/calc/BoltTorqueForm"
import Link from "next/link"
import { ChevronLeft } from "lucide-react"

export const metadata = { title: "Bolt Torque — EngBrain" }

export default function BoltTorquePage() {
  return (
    <div className="p-4">
      <Link href="/calc" className="flex items-center gap-1 text-sm text-white/50 hover:text-white/80 mb-4 transition-colors">
        <ChevronLeft size={16} /> Back to Calculators
      </Link>
      <h1 className="text-xl font-bold text-white mb-1">Bolt Torque Calculator</h1>
      <p className="text-sm text-white/50 mb-6">Tightening torque, preload force and proof load</p>
      <BoltTorqueForm />
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add apps/web/components/calc/BoltTorqueForm.tsx apps/web/app/(app)/calc/bolt-torque/page.tsx
git commit -m "feat: add bolt torque calculator UI"
```

---

## Task 10: Frontend — Material Selection UI

**Files:**
- Create: `apps/web/components/calc/MaterialSelectionForm.tsx`
- Create: `apps/web/app/(app)/calc/material-selection/page.tsx`

**Step 1: Create the form**

```tsx
// apps/web/components/calc/MaterialSelectionForm.tsx
"use client"
import { useState } from "react"
import { toast } from "sonner"
import { api, ApiError } from "@/lib/api"
import { useSession } from "@/lib/useSession"

const FLUIDS = [
  { value: "water", label: "Water" },
  { value: "seawater", label: "Seawater" },
  { value: "sulfuric_acid", label: "Sulfuric Acid (H₂SO₄)" },
  { value: "hydrochloric_acid", label: "Hydrochloric Acid (HCl)" },
  { value: "caustic_soda", label: "Caustic Soda (NaOH)" },
  { value: "diesel", label: "Diesel / Fuel Oil" },
]

const RATING_STYLE: Record<string, string> = {
  recommended: "bg-green-900/30 text-green-400 border-green-500/30",
  conditional:  "bg-yellow-900/30 text-yellow-400 border-yellow-500/30",
  incompatible: "bg-red-900/30 text-red-400 border-red-500/30",
}

interface MaterialEntry { material: string; rating: string; note: string }
interface ComponentResult { component: string; materials: MaterialEntry[] }
interface SelectionResult { fluid: string; components: ComponentResult[] }

const COMPONENT_LABELS: Record<string, string> = {
  casing: "Casing", impeller: "Impeller", wear_ring: "Wear Ring",
  shaft: "Shaft", mechanical_seal: "Mechanical Seal",
}

export function MaterialSelectionForm() {
  const { token } = useSession()
  const [fluid, setFluid] = useState("")
  const [concentration, setConcentration] = useState("100")
  const [temp, setTemp] = useState("25")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<SelectionResult | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!token || !fluid) { toast.error("Select a fluid and log in"); return }
    setLoading(true)
    try {
      const data = await api.materialSelection({ fluid, concentration_pct: Number(concentration), temp_c: Number(temp) }, token) as SelectionResult
      setResult(data)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Request failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-1">
          <label className="block text-sm font-medium text-white/80">Fluid</label>
          <select value={fluid} onChange={e => { setFluid(e.target.value); setResult(null) }} className="w-full h-12 px-3 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:border-blue-500">
            <option value="">Select fluid...</option>
            {FLUIDS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="block text-sm font-medium text-white/80">Concentration (%)</label>
            <input type="text" inputMode="decimal" value={concentration} onChange={e => setConcentration(e.target.value)} className="w-full h-12 px-3 rounded-lg bg-white/5 border border-white/10 text-white text-lg focus:outline-none focus:border-blue-500" />
          </div>
          <div className="space-y-1">
            <label className="block text-sm font-medium text-white/80">Temperature (°C)</label>
            <input type="text" inputMode="decimal" value={temp} onChange={e => setTemp(e.target.value)} className="w-full h-12 px-3 rounded-lg bg-white/5 border border-white/10 text-white text-lg focus:outline-none focus:border-blue-500" />
          </div>
        </div>
        <button type="submit" disabled={loading || !fluid} className="w-full h-12 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium transition-colors">
          {loading ? "Loading..." : "Get Material Recommendations"}
        </button>
      </form>

      {result && (
        <div className="space-y-4">
          {result.components.map(comp => (
            <div key={comp.component} className="rounded-lg border border-white/10 overflow-hidden" style={{ backgroundColor: "#1A1D27" }}>
              <div className="p-3 border-b border-white/10">
                <h3 className="text-sm font-semibold text-white">{COMPONENT_LABELS[comp.component] ?? comp.component}</h3>
              </div>
              <div className="divide-y divide-white/5">
                {comp.materials.map(m => (
                  <div key={m.material} className="flex items-center justify-between p-3">
                    <div>
                      <p className="text-sm text-white">{m.material}</p>
                      {m.note && <p className="text-xs text-white/40 mt-0.5">{m.note}</p>}
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded-full border font-medium capitalize ${RATING_STYLE[m.rating] ?? ""}`}>
                      {m.rating}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

```tsx
// apps/web/app/(app)/calc/material-selection/page.tsx
import { MaterialSelectionForm } from "@/components/calc/MaterialSelectionForm"
import Link from "next/link"
import { ChevronLeft } from "lucide-react"

export const metadata = { title: "Material Selection — EngBrain" }

export default function MaterialSelectionPage() {
  return (
    <div className="p-4">
      <Link href="/calc" className="flex items-center gap-1 text-sm text-white/50 hover:text-white/80 mb-4 transition-colors">
        <ChevronLeft size={16} /> Back to Calculators
      </Link>
      <h1 className="text-xl font-bold text-white mb-1">Material Selection</h1>
      <p className="text-sm text-white/50 mb-6">Compatible materials by fluid, concentration and temperature</p>
      <MaterialSelectionForm />
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add apps/web/components/calc/MaterialSelectionForm.tsx apps/web/app/(app)/calc/material-selection/page.tsx
git commit -m "feat: add material selection UI"
```

---

## Task 11: Frontend — Parallel Pumps UI

This is the most complex frontend task. Install Recharts first if not present.

**Files:**
- Create: `apps/web/components/calc/ParallelPumpsForm.tsx`
- Create: `apps/web/app/(app)/calc/parallel-pumps/page.tsx`

**Step 1: Check if Recharts is installed**

```bash
cd apps/web && cat package.json | grep recharts
```

If not present:
```bash
cd apps/web && npm install recharts
```

**Step 2: Create the form component**

```tsx
// apps/web/components/calc/ParallelPumpsForm.tsx
"use client"
import { useState, useRef } from "react"
import { toast } from "sonner"
import { api, ApiError } from "@/lib/api"
import { useSession } from "@/lib/useSession"
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, ResponsiveContainer,
} from "recharts"

interface HQPoint { q: number; h: number }
interface PumpData { name: string; points: HQPoint[]; bep_q: string }
interface PumpResult { name: string; q: number; h: number; bep_ratio: number | null; alert: string | null }
interface ParallelResult {
  operating_point: { q_total: number; h: number }
  pumps: PumpResult[]
  combined_curve_points: HQPoint[]
  system_curve_points: HQPoint[]
  individual_curve_points: HQPoint[][]
}

const PUMP_COLORS = ["#0066FF", "#00C853", "#FF6B35", "#A855F7"]
const EMPTY_PUMP = (): PumpData => ({ name: "", points: [{ q: 0, h: 0 }, { q: 0, h: 0 }, { q: 0, h: 0 }], bep_q: "" })

export function ParallelPumpsForm() {
  const { token } = useSession()
  const [pumps, setPumps] = useState<PumpData[]>([EMPTY_PUMP()])
  const [staticHead, setStaticHead] = useState("5")
  const [resistance, setResistance] = useState("0.04")
  const [loading, setLoading] = useState(false)
  const [extracting, setExtracting] = useState<number | null>(null)
  const [result, setResult] = useState<ParallelResult | null>(null)
  const fileRefs = useRef<(HTMLInputElement | null)[]>([])

  function updatePump(i: number, field: keyof PumpData, value: string) {
    setPumps(prev => prev.map((p, idx) => idx === i ? { ...p, [field]: value } : p))
  }

  function updatePoint(pumpIdx: number, ptIdx: number, field: "q" | "h", value: string) {
    setPumps(prev => prev.map((p, i) => {
      if (i !== pumpIdx) return p
      const pts = p.points.map((pt, j) => j === ptIdx ? { ...pt, [field]: Number(value) } : pt)
      return { ...p, points: pts }
    }))
  }

  function addPoint(pumpIdx: number) {
    setPumps(prev => prev.map((p, i) => i === pumpIdx ? { ...p, points: [...p.points, { q: 0, h: 0 }] } : p))
  }

  function removePoint(pumpIdx: number, ptIdx: number) {
    setPumps(prev => prev.map((p, i) => {
      if (i !== pumpIdx || p.points.length <= 3) return p
      return { ...p, points: p.points.filter((_, j) => j !== ptIdx) }
    }))
  }

  function addPump() {
    if (pumps.length >= 4) return
    setPumps(prev => [...prev, EMPTY_PUMP()])
  }

  function removePump(i: number) {
    if (pumps.length <= 1) return
    setPumps(prev => prev.filter((_, idx) => idx !== i))
  }

  async function extractCurve(pumpIdx: number, file: File) {
    if (!token) { toast.error("Please log in"); return }
    setExtracting(pumpIdx)
    try {
      const formData = new FormData()
      formData.append("file", file)
      const data = await api.extractPumpCurve(formData, token) as { points: HQPoint[] }
      setPumps(prev => prev.map((p, i) => i === pumpIdx ? { ...p, points: data.points } : p))
      toast.success(`Extracted ${data.points.length} points from datasheet`)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Extraction failed — enter points manually")
    } finally {
      setExtracting(null)
    }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!token) { toast.error("Please log in"); return }
    setLoading(true)
    try {
      const body = {
        pumps: pumps.map(p => ({
          name: p.name || "Pump",
          points: p.points,
          bep_q: p.bep_q ? Number(p.bep_q) : null,
        })),
        system_curve: { static_head: Number(staticHead), resistance: Number(resistance) },
      }
      const data = await api.parallelPumps(body, token) as ParallelResult
      setResult(data)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Calculation failed")
    } finally {
      setLoading(false)
    }
  }

  // Build chart data: merge all curves by Q index
  const chartData = result ? (() => {
    const points: Record<string, number>[] = result.combined_curve_points.map(pt => ({
      q: pt.q, "Combined": pt.h,
    }))
    result.system_curve_points.forEach((pt, i) => {
      if (points[i]) points[i]["System"] = pt.h
    })
    result.individual_curve_points.forEach((curve, ci) => {
      curve.forEach((pt, i) => {
        if (points[i]) points[i][result.pumps[ci]?.name ?? `Pump ${ci + 1}`] = pt.h
      })
    })
    return points
  })() : []

  const ALERT_LABEL: Record<string, string> = {
    off_curve: "Off BEP", reverse_flow: "Reverse Flow",
  }

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="space-y-6">
        {/* Pumps */}
        {pumps.map((pump, pi) => (
          <div key={pi} className="rounded-lg border border-white/10 p-4 space-y-4" style={{ backgroundColor: "#1A1D27" }}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: PUMP_COLORS[pi] }} />
                <span className="text-sm font-semibold text-white">Pump {pi + 1}</span>
              </div>
              {pumps.length > 1 && (
                <button type="button" onClick={() => removePump(pi)} className="text-xs text-red-400 hover:text-red-300">Remove</button>
              )}
            </div>

            <input
              type="text"
              placeholder="Pump name / tag (optional)"
              value={pump.name}
              onChange={e => updatePump(pi, "name", e.target.value)}
              className="w-full h-10 px-3 rounded-lg bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-blue-500"
            />

            {/* Upload */}
            <div>
              <input
                type="file"
                accept="image/*,.pdf"
                ref={el => { fileRefs.current[pi] = el }}
                className="hidden"
                onChange={e => { const f = e.target.files?.[0]; if (f) extractCurve(pi, f) }}
              />
              <button
                type="button"
                onClick={() => fileRefs.current[pi]?.click()}
                disabled={extracting === pi}
                className="w-full h-10 rounded-lg border border-dashed border-white/20 text-white/50 text-sm hover:border-blue-500/50 hover:text-white/70 transition-colors disabled:opacity-50"
              >
                {extracting === pi ? "Extracting curve..." : "Upload datasheet (PDF or image) to auto-fill"}
              </button>
            </div>

            {/* H-Q table */}
            <div>
              <div className="grid grid-cols-[1fr_1fr_auto] gap-2 mb-2">
                <span className="text-xs text-white/40 text-center">Q (m³/h)</span>
                <span className="text-xs text-white/40 text-center">H (m)</span>
                <span className="w-6" />
              </div>
              {pump.points.map((pt, ptIdx) => (
                <div key={ptIdx} className="grid grid-cols-[1fr_1fr_auto] gap-2 mb-2">
                  <input type="number" step="any" value={pt.q} onChange={e => updatePoint(pi, ptIdx, "q", e.target.value)}
                    className="h-10 px-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-blue-500 text-center" />
                  <input type="number" step="any" value={pt.h} onChange={e => updatePoint(pi, ptIdx, "h", e.target.value)}
                    className="h-10 px-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-blue-500 text-center" />
                  <button type="button" onClick={() => removePoint(pi, ptIdx)} className="w-6 h-10 text-white/30 hover:text-red-400 text-lg leading-none">×</button>
                </div>
              ))}
              <button type="button" onClick={() => addPoint(pi)} className="text-xs text-blue-400 hover:text-blue-300">+ Add point</button>
            </div>

            <input
              type="text"
              inputMode="decimal"
              placeholder="BEP flow — Best Efficiency Point Q (m³/h) — optional"
              value={pump.bep_q}
              onChange={e => updatePump(pi, "bep_q", e.target.value)}
              className="w-full h-10 px-3 rounded-lg bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-blue-500 placeholder:text-white/30"
            />
          </div>
        ))}

        {pumps.length < 4 && (
          <button type="button" onClick={addPump} className="w-full h-10 rounded-lg border border-dashed border-blue-500/30 text-blue-400 text-sm hover:border-blue-500/60 transition-colors">
            + Add pump
          </button>
        )}

        {/* System curve */}
        <div className="rounded-lg border border-white/10 p-4 space-y-3" style={{ backgroundColor: "#1A1D27" }}>
          <h3 className="text-sm font-semibold text-white">System Curve — H = H_static + R × Q²</h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs text-white/50">Static Head (m)</label>
              <input type="text" inputMode="decimal" value={staticHead} onChange={e => setStaticHead(e.target.value)}
                className="w-full h-10 px-3 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:border-blue-500" />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-white/50">Resistance R</label>
              <input type="text" inputMode="decimal" value={resistance} onChange={e => setResistance(e.target.value)}
                className="w-full h-10 px-3 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:border-blue-500" />
            </div>
          </div>
        </div>

        <button type="submit" disabled={loading}
          className="w-full h-12 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium transition-colors">
          {loading ? "Calculating..." : "Calculate Operating Point"}
        </button>
      </form>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Operating point */}
          <div className="rounded-lg border border-white/10 p-4" style={{ backgroundColor: "#1A1D27" }}>
            <h3 className="text-sm font-semibold text-white mb-3">System Operating Point</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-white/40">Total Flow</p>
                <p className="text-3xl font-bold text-blue-400">{result.operating_point.q_total} <span className="text-lg font-normal text-white/50">m³/h</span></p>
              </div>
              <div>
                <p className="text-xs text-white/40">Operating Head</p>
                <p className="text-3xl font-bold text-blue-400">{result.operating_point.h} <span className="text-lg font-normal text-white/50">m</span></p>
              </div>
            </div>
          </div>

          {/* Per-pump table */}
          <div className="rounded-lg border border-white/10 overflow-hidden" style={{ backgroundColor: "#1A1D27" }}>
            <div className="p-3 border-b border-white/10">
              <h3 className="text-sm font-semibold text-white">Individual Pump Results</h3>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="p-3 text-left text-white/40 font-medium">Pump</th>
                  <th className="p-3 text-right text-white/40 font-medium">Q (m³/h)</th>
                  <th className="p-3 text-right text-white/40 font-medium">BEP%</th>
                  <th className="p-3 text-right text-white/40 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {result.pumps.map((p, i) => (
                  <tr key={i} className="border-b border-white/5 last:border-0">
                    <td className="p-3 text-white flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: PUMP_COLORS[i] }} />
                      {p.name}
                    </td>
                    <td className="p-3 text-right text-white">{p.q}</td>
                    <td className="p-3 text-right text-white/60">
                      {p.bep_ratio != null ? `${(p.bep_ratio * 100).toFixed(0)}%` : "—"}
                    </td>
                    <td className="p-3 text-right">
                      {p.alert ? (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-red-900/30 text-red-400 border border-red-500/30">
                          {ALERT_LABEL[p.alert] ?? p.alert}
                        </span>
                      ) : (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-green-900/30 text-green-400 border border-green-500/30">OK</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Chart */}
          <div className="rounded-lg border border-white/10 p-4" style={{ backgroundColor: "#1A1D27" }}>
            <h3 className="text-sm font-semibold text-white mb-4">Performance Curves</h3>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="q" stroke="rgba(255,255,255,0.3)" tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} label={{ value: "Q (m³/h)", position: "insideBottom", offset: -2, fill: "rgba(255,255,255,0.3)", fontSize: 11 }} />
                <YAxis stroke="rgba(255,255,255,0.3)" tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} label={{ value: "H (m)", angle: -90, position: "insideLeft", fill: "rgba(255,255,255,0.3)", fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: "#1A1D27", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }} labelStyle={{ color: "rgba(255,255,255,0.6)" }} itemStyle={{ color: "rgba(255,255,255,0.8)" }} />
                <Legend wrapperStyle={{ fontSize: 11, color: "rgba(255,255,255,0.5)" }} />
                {result.pumps.map((p, i) => (
                  <Line key={p.name} type="monotone" dataKey={p.name} stroke={PUMP_COLORS[i]} strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
                ))}
                <Line type="monotone" dataKey="Combined" stroke="#FFFFFF" strokeWidth={2.5} dot={false} />
                <Line type="monotone" dataKey="System" stroke="#FF6B35" strokeWidth={2} dot={false} />
                <ReferenceLine x={result.operating_point.q_total} stroke="rgba(255,255,255,0.3)" strokeDasharray="3 3" />
                <ReferenceLine y={result.operating_point.h} stroke="rgba(255,255,255,0.3)" strokeDasharray="3 3" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  )
}
```

```tsx
// apps/web/app/(app)/calc/parallel-pumps/page.tsx
import { ParallelPumpsForm } from "@/components/calc/ParallelPumpsForm"
import Link from "next/link"
import { ChevronLeft } from "lucide-react"

export const metadata = { title: "Parallel Pumps — EngBrain" }

export default function ParallelPumpsPage() {
  return (
    <div className="p-4">
      <Link href="/calc" className="flex items-center gap-1 text-sm text-white/50 hover:text-white/80 mb-4 transition-colors">
        <ChevronLeft size={16} /> Back to Calculators
      </Link>
      <h1 className="text-xl font-bold text-white mb-1">Parallel Pump Association</h1>
      <p className="text-sm text-white/50 mb-6">Find the operating point for multiple pumps in parallel — including different pump models</p>
      <ParallelPumpsForm />
    </div>
  )
}
```

**Step 3: Commit**

```bash
git add apps/web/components/calc/ParallelPumpsForm.tsx apps/web/app/(app)/calc/parallel-pumps/page.tsx
git commit -m "feat: add parallel pump association UI with chart and datasheet upload"
```

---

## Task 12: Update Calculator Index Page

**Files:**
- Modify: `apps/web/app/(app)/calc/page.tsx`

**Step 1: Update the CALCULATORS list**

Replace the `CALCULATORS` array in `apps/web/app/(app)/calc/page.tsx`:

```typescript
const CALCULATORS = [
  {
    href: "/calc/parallel-pumps",
    title: "Parallel Pump Association",
    description: "Operating point for multiple pumps in parallel — including different models",
    badge: "New",
  },
  {
    href: "/calc/npsh",
    title: "NPSH Calculator",
    description: "Net Positive Suction Head — prevent cavitation",
    badge: "Essential",
  },
  {
    href: "/calc/material-selection",
    title: "Material Selection",
    description: "Compatible materials by fluid, concentration and temperature",
    badge: "New",
  },
  {
    href: "/calc/galvanic",
    title: "Galvanic Corrosion Check",
    description: "Assess compatibility between two materials in contact",
    badge: "New",
  },
  {
    href: "/calc/bolt-torque",
    title: "Bolt Torque Calculator",
    description: "Tightening torque and preload by grade, diameter and condition",
    badge: "New",
  },
  {
    href: "/calc/flanges",
    title: "ASME B16.5 Flanges",
    description: "Flange dimensions by NPS and pressure class",
    badge: "New",
  },
  {
    href: "/calc/head-loss",
    title: "Head Loss",
    description: "Darcy-Weisbach friction losses in piping",
    badge: null,
  },
  {
    href: "/calc/convert",
    title: "Unit Converter",
    description: "GPM, bar, kPa, m³/h and more",
    badge: null,
  },
]
```

**Step 2: Commit**

```bash
git add apps/web/app/(app)/calc/page.tsx
git commit -m "feat: update calculator index with 5 new modules"
```

---

## Final Verification

Run all backend tests:

```bash
cd apps/api && python -m pytest tests/ -v
```

Expected: all tests pass, including new parallel pumps, bolt torque, material selection, and curve extraction tests.

Start the dev server and manually verify:
```bash
# Terminal 1
cd apps/api && uvicorn app.main:app --reload

# Terminal 2
cd apps/web && npm run dev
```

Navigate to `/calc` and verify all 5 new calculators appear and work.
