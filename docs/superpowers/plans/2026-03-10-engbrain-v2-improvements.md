# EngBrain v2 Improvements Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix NPSHa naming, add kg/cm² support with pressure unit selector, add temperature-aware material selection (safety-critical), add fluid presets for NPSH, improve material notes visibility.

**Architecture:** Backend stays SI-only — all unit conversion happens in frontend before API calls. Material selection gets temperature/concentration limits per material entry. New `fluid_properties.py` service provides water/diesel/etc properties by temperature.

**Tech Stack:** Python/FastAPI (backend), React/Next.js/TypeScript (frontend), Pint (units), pytest (tests)

---

## Chunk 1: Quick Fixes + Backend Foundation

### Task 1: Fix NPSHa Title in i18n (3 files)

**Files:**
- Modify: `apps/web/i18n/en.json:15-16`
- Modify: `apps/web/i18n/pt.json:15-18`
- Modify: `apps/web/i18n/es.json:15-18`

- [ ] **Step 1: Update EN translations**

In `apps/web/i18n/en.json`, change:
```json
"npsh": {
  "title": "NPSHa Calculator",
  "description": "Net Positive Suction Head Available — prevent cavitation",
  "subtitle": "Net Positive Suction Head Available",
```

- [ ] **Step 2: Update PT translations**

In `apps/web/i18n/pt.json`, change:
```json
"npsh": {
  "title": "Calculadora NPSHa",
  "description": "NPSH disponível — prevenir cavitação",
  "subtitle": "NPSH disponível",
  "result": "Resultado NPSHa",
  "safe": "Seguro",
  "risk": "Risco de Cavitação",
  "calculate": "Calcular NPSHa",
```

- [ ] **Step 3: Update ES translations**

In `apps/web/i18n/es.json`, change:
```json
"npsh": {
  "title": "Calculadora NPSHa",
  "description": "NPSH disponible — prevenir cavitación",
  "subtitle": "NPSH disponible",
  "result": "Resultado NPSHa",
  "safe": "Seguro",
  "risk": "Riesgo de Cavitación",
  "calculate": "Calcular NPSHa",
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/i18n/en.json apps/web/i18n/pt.json apps/web/i18n/es.json
git commit -m "fix: rename NPSH to NPSHa in all i18n files"
```

### Task 2: Add kg/cm² to Backend Unit Map

**Files:**
- Modify: `apps/api/app/services/units.py:10-32`
- Modify: `apps/api/tests/test_units.py`

- [ ] **Step 1: Write failing test for kg/cm² conversion**

Add to `apps/api/tests/test_units.py`:
```python
def test_pressure_kgcm2_to_kpa():
    result = convert_unit(1.0, "kgf/cm2", "kPa")
    assert abs(result - 98.0665) < 0.01


def test_pressure_kpa_to_kgcm2():
    result = convert_unit(101.325, "kPa", "kgf/cm2")
    assert abs(result - 1.0332) < 0.01
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_units.py::test_pressure_kgcm2_to_kpa -v`
Expected: FAIL with ConversionError (unknown unit)

- [ ] **Step 3: Add kg/cm² to UNIT_MAP**

In `apps/api/app/services/units.py`, add after the `"MPa"` line:
```python
    "kgf/cm2": "kilogram_force / centimeter**2",
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd apps/api && python -m pytest tests/test_units.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/services/units.py apps/api/tests/test_units.py
git commit -m "feat: add kgf/cm2 pressure unit to unit converter"
```

### Task 3: Fluid Properties Service (Backend)

**Files:**
- Create: `apps/api/app/services/fluid_properties.py`
- Create: `apps/api/tests/test_fluid_properties.py`

- [ ] **Step 1: Write failing tests for fluid properties**

Create `apps/api/tests/test_fluid_properties.py`:
```python
import pytest
from app.services.fluid_properties import get_fluid_properties, FluidProperties


def test_water_at_20c():
    props = get_fluid_properties("water", 20.0)
    assert abs(props.density_kg_m3 - 998.2) < 1.0
    assert abs(props.vapor_pressure_kpa - 2.338) < 0.1


def test_water_at_100c():
    props = get_fluid_properties("water", 100.0)
    assert abs(props.density_kg_m3 - 958.4) < 1.0
    assert abs(props.vapor_pressure_kpa - 101.325) < 1.0


def test_water_at_60c():
    props = get_fluid_properties("water", 60.0)
    assert abs(props.density_kg_m3 - 983.2) < 2.0
    assert abs(props.vapor_pressure_kpa - 19.94) < 1.0


def test_water_interpolates_between_points():
    """Temperature between table entries should interpolate."""
    props = get_fluid_properties("water", 25.0)
    assert 995 < props.density_kg_m3 < 999
    assert 2.3 < props.vapor_pressure_kpa < 4.0


def test_diesel_at_25c():
    props = get_fluid_properties("diesel", 25.0)
    assert 820 < props.density_kg_m3 < 860
    assert props.vapor_pressure_kpa < 1.0


def test_unknown_fluid_raises():
    with pytest.raises(ValueError, match="Unknown fluid"):
        get_fluid_properties("__unknown__", 25.0)


def test_available_fluids():
    from app.services.fluid_properties import AVAILABLE_FLUIDS
    assert "water" in AVAILABLE_FLUIDS
    assert "diesel" in AVAILABLE_FLUIDS
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/api && python -m pytest tests/test_fluid_properties.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement fluid properties service**

Create `apps/api/app/services/fluid_properties.py`:
```python
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

# Diesel/fuel oil: relatively stable properties
_DIESEL_TABLE: list[tuple[float, float, float]] = [
    (0.0, 860.0, 0.01),
    (20.0, 845.0, 0.05),
    (40.0, 830.0, 0.15),
    (60.0, 815.0, 0.40),
    (80.0, 800.0, 1.00),
    (100.0, 785.0, 2.50),
]

# Seawater (3.5% salinity): similar to water but slightly denser
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd apps/api && python -m pytest tests/test_fluid_properties.py -v`
Expected: ALL PASS

- [ ] **Step 5: Add endpoint to calculations router**

Add to `apps/api/app/routers/calculations.py` after the material-selection endpoint:

```python
from app.services.fluid_properties import get_fluid_properties, AVAILABLE_FLUIDS

class FluidPropertiesRequest(BaseModel):
    fluid: str
    temp_c: float = Field(..., ge=-10, le=200)


@router.post("/fluid-properties")
async def fluid_properties(req: FluidPropertiesRequest, user: dict = Depends(get_current_user)):
    try:
        props = get_fluid_properties(req.fluid, req.temp_c)
        return {
            "fluid": props.fluid,
            "temp_c": props.temp_c,
            "density_kg_m3": props.density_kg_m3,
            "vapor_pressure_kpa": props.vapor_pressure_kpa,
            "available_fluids": AVAILABLE_FLUIDS,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

- [ ] **Step 6: Add endpoint test**

Add to `apps/api/tests/test_fluid_properties.py`:
```python
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_fluid_properties_endpoint(mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/fluid-properties", json={
            "fluid": "water",
            "temp_c": 20.0,
        })
    assert response.status_code == 200
    data = response.json()
    assert abs(data["density_kg_m3"] - 998.2) < 1.0
    assert abs(data["vapor_pressure_kpa"] - 2.338) < 0.1
    assert "water" in data["available_fluids"]


@pytest.mark.asyncio
async def test_fluid_properties_unknown_fluid_returns_400(mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/fluid-properties", json={
            "fluid": "lava",
            "temp_c": 20.0,
        })
    assert response.status_code == 400
```

- [ ] **Step 7: Run all tests**

Run: `cd apps/api && python -m pytest tests/test_fluid_properties.py -v`
Expected: ALL PASS

- [ ] **Step 8: Commit**

```bash
git add apps/api/app/services/fluid_properties.py apps/api/tests/test_fluid_properties.py apps/api/app/routers/calculations.py
git commit -m "feat: add fluid properties service with water/diesel/seawater tables"
```

---

## Chunk 2: Temperature-Aware Material Selection (Safety-Critical)

### Task 4: Refactor Material Selection with Temperature/Concentration Limits

**Files:**
- Modify: `apps/api/app/services/material_selection.py`
- Modify: `apps/api/tests/test_material_selection.py`

- [ ] **Step 1: Write failing tests for temperature filtering**

Add to `apps/api/tests/test_material_selection.py`:
```python
def test_carbon_steel_caustic_soda_below_60c_recommended():
    """Carbon steel in caustic soda below 60°C should be recommended."""
    result = select_materials(fluid="caustic_soda", concentration_pct=50.0, temp_c=40.0)
    casing = next(r for r in result if r.component == "casing")
    cs = next(m for m in casing.materials if m.material == "Carbon Steel")
    assert cs.rating == "recommended"


def test_carbon_steel_caustic_soda_above_60c_incompatible():
    """Carbon steel in caustic soda above 60°C should be incompatible."""
    result = select_materials(fluid="caustic_soda", concentration_pct=50.0, temp_c=80.0)
    casing = next(r for r in result if r.component == "casing")
    cs = next(m for m in casing.materials if m.material == "Carbon Steel")
    assert cs.rating == "incompatible"


def test_carbon_steel_caustic_soda_above_60c_has_note():
    """Incompatible materials should explain why."""
    result = select_materials(fluid="caustic_soda", concentration_pct=50.0, temp_c=80.0)
    casing = next(r for r in result if r.component == "casing")
    cs = next(m for m in casing.materials if m.material == "Carbon Steel")
    assert "60" in cs.note  # should mention the temperature limit


def test_sulfuric_acid_ss316_mid_concentration_incompatible():
    """SS 316 in sulfuric acid at 30% concentration should be incompatible."""
    result = select_materials(fluid="sulfuric_acid", concentration_pct=30.0, temp_c=25.0)
    casing = next(r for r in result if r.component == "casing")
    ss316 = next(m for m in casing.materials if m.material == "SS 316")
    assert ss316.rating == "incompatible"


def test_sulfuric_acid_ss316_low_concentration_conditional():
    """SS 316 in sulfuric acid at 3% concentration should remain conditional."""
    result = select_materials(fluid="sulfuric_acid", concentration_pct=3.0, temp_c=25.0)
    casing = next(r for r in result if r.component == "casing")
    ss316 = next(m for m in casing.materials if m.material == "SS 316")
    assert ss316.rating == "conditional"


def test_nbr_caustic_soda_above_40c_incompatible():
    """NBR in caustic soda above 40°C should be incompatible."""
    result = select_materials(fluid="caustic_soda", concentration_pct=50.0, temp_c=50.0)
    orings = next(r for r in result if r.component == "o_rings")
    nbr = next(m for m in orings.materials if m.material == "NBR")
    assert nbr.rating == "incompatible"


def test_water_carbon_steel_casing_present():
    """Carbon steel should appear for water casing (conditional, with coating)."""
    result = select_materials(fluid="water", concentration_pct=100.0, temp_c=25.0)
    casing = next(r for r in result if r.component == "casing")
    materials = [m.material for m in casing.materials]
    assert "Carbon Steel" in materials
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/api && python -m pytest tests/test_material_selection.py::test_carbon_steel_caustic_soda_above_60c_incompatible -v`
Expected: FAIL (returns "recommended" regardless of temp)

- [ ] **Step 3: Refactor material_selection.py with temperature/concentration limits**

Replace `apps/api/app/services/material_selection.py` with:
```python
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


@dataclass
class _MaterialEntry:
    """Internal entry with limits for temperature/concentration filtering."""
    rating: Rating
    note: str
    max_temp_c: float | None = None       # above this → incompatible
    min_conc_pct: float | None = None      # below this → incompatible
    max_conc_pct: float | None = None      # above this → incompatible


def _e(rating: Rating, note: str = "",
       max_temp: float | None = None,
       min_conc: float | None = None,
       max_conc: float | None = None) -> _MaterialEntry:
    return _MaterialEntry(rating=rating, note=note,
                          max_temp_c=max_temp, min_conc_pct=min_conc, max_conc_pct=max_conc)


_TABLE: dict[str, dict[str, dict[str, _MaterialEntry]]] = {
    "water": {
        "casing": {
            "Cast Iron": _e("recommended"),
            "SS 316": _e("recommended"),
            "Bronze": _e("recommended"),
            "Duplex SS": _e("recommended"),
            "Carbon Steel": _e("conditional", "use with coating"),
        },
        "impeller": {
            "Cast Iron": _e("recommended"),
            "SS 316": _e("recommended"),
            "Bronze": _e("recommended"),
            "Duplex SS": _e("recommended"),
            "Carbon Steel": _e("conditional", "use with coating"),
        },
        "wear_ring": {
            "Cast Iron": _e("recommended"),
            "SS 316": _e("recommended"),
            "Bronze": _e("recommended"),
            "Duplex SS": _e("recommended"),
        },
        "shaft": {
            "SS 316": _e("recommended"),
            "Alloy 20": _e("recommended"),
            "Carbon Steel": _e("conditional", "use with coating"),
        },
        "mechanical_seal": {
            "Carbon/SiC": _e("recommended"),
            "Carbon/Ceramic": _e("recommended"),
            "Viton": _e("recommended"),
            "EPDM": _e("recommended"),
        },
        "o_rings": {
            "Viton": _e("recommended"),
            "EPDM": _e("recommended"),
            "NBR": _e("recommended"),
            "PTFE": _e("recommended"),
        },
    },
    "seawater": {
        "casing": {
            "Cast Iron": _e("conditional", "risk of corrosion without coating"),
            "SS 316": _e("recommended"),
            "Bronze": _e("recommended"),
            "Duplex SS": _e("recommended"),
            "Super Duplex": _e("recommended"),
        },
        "impeller": {
            "Cast Iron": _e("incompatible", "galvanic corrosion risk"),
            "SS 316": _e("conditional", "check chloride levels"),
            "Bronze": _e("recommended"),
            "Duplex SS": _e("recommended"),
            "Super Duplex": _e("recommended"),
        },
        "wear_ring": {
            "SS 316": _e("conditional"),
            "Bronze": _e("recommended"),
            "Super Duplex": _e("recommended"),
        },
        "shaft": {
            "SS 316": _e("conditional", "pitting risk"),
            "Duplex SS": _e("recommended"),
            "Super Duplex": _e("recommended"),
        },
        "mechanical_seal": {
            "SiC/SiC": _e("recommended"),
            "Carbon/SiC": _e("recommended"),
            "Viton": _e("recommended"),
            "EPDM": _e("incompatible"),
        },
        "o_rings": {
            "Viton": _e("recommended"),
            "EPDM": _e("conditional", "check temp", max_temp=60.0),
            "NBR": _e("conditional", "limited life"),
            "PTFE": _e("recommended"),
        },
    },
    "sulfuric_acid": {
        "casing": {
            "Cast Iron": _e("incompatible"),
            "SS 316": _e("conditional", "only < 5% or > 93% concentration", max_conc=5.0),
            "Alloy 20": _e("recommended"),
            "Hastelloy C": _e("recommended"),
            "PTFE-lined": _e("recommended"),
        },
        "impeller": {
            "Cast Iron": _e("incompatible"),
            "SS 316": _e("conditional", "narrow concentration range", max_conc=5.0),
            "Alloy 20": _e("recommended"),
            "Hastelloy C": _e("recommended"),
        },
        "wear_ring": {
            "SS 316": _e("conditional", max_conc=5.0),
            "Alloy 20": _e("recommended"),
            "Hastelloy C": _e("recommended"),
        },
        "shaft": {
            "SS 316": _e("conditional", max_conc=5.0),
            "Alloy 20": _e("recommended"),
            "Hastelloy C": _e("recommended"),
        },
        "mechanical_seal": {
            "SiC/SiC": _e("recommended"),
            "Carbon/SiC": _e("conditional", "< 60% concentration", max_conc=60.0),
            "PTFE": _e("recommended"),
            "Viton": _e("incompatible"),
        },
        "o_rings": {
            "PTFE": _e("recommended"),
            "Viton": _e("conditional", "< 70% concentration", max_conc=70.0),
            "EPDM": _e("incompatible"),
            "NBR": _e("incompatible"),
        },
    },
    "hydrochloric_acid": {
        "casing": {
            "Cast Iron": _e("incompatible"),
            "SS 316": _e("incompatible"),
            "Hastelloy C": _e("recommended"),
            "Rubber-lined": _e("recommended"),
            "PTFE-lined": _e("recommended"),
        },
        "impeller": {
            "Cast Iron": _e("incompatible"),
            "SS 316": _e("incompatible"),
            "Hastelloy C": _e("recommended"),
            "Rubber": _e("recommended", "< 60°C", max_temp=60.0),
        },
        "wear_ring": {
            "Hastelloy C": _e("recommended"),
            "PTFE": _e("recommended"),
        },
        "shaft": {
            "Hastelloy C": _e("recommended"),
            "SS 316": _e("incompatible"),
        },
        "mechanical_seal": {
            "SiC/SiC": _e("recommended"),
            "Carbon/SiC": _e("incompatible"),
            "PTFE": _e("recommended"),
            "Viton": _e("incompatible"),
        },
        "o_rings": {
            "PTFE": _e("recommended"),
            "Viton": _e("incompatible"),
            "EPDM": _e("incompatible"),
            "NBR": _e("incompatible"),
        },
    },
    "caustic_soda": {
        "casing": {
            "Cast Iron": _e("recommended"),
            "SS 316": _e("recommended"),
            "Carbon Steel": _e("recommended", "< 60°C", max_temp=60.0),
            "Duplex SS": _e("recommended"),
        },
        "impeller": {
            "Cast Iron": _e("recommended"),
            "SS 316": _e("recommended"),
            "Carbon Steel": _e("conditional", "< 60°C", max_temp=60.0),
            "Duplex SS": _e("recommended"),
        },
        "wear_ring": {
            "Cast Iron": _e("recommended"),
            "SS 316": _e("recommended"),
        },
        "shaft": {
            "SS 316": _e("recommended"),
            "Carbon Steel": _e("conditional", "< 60°C", max_temp=60.0),
        },
        "mechanical_seal": {
            "Carbon/SiC": _e("recommended"),
            "SiC/SiC": _e("recommended"),
            "EPDM": _e("recommended"),
            "Viton": _e("incompatible"),
        },
        "o_rings": {
            "EPDM": _e("recommended"),
            "PTFE": _e("recommended"),
            "Viton": _e("incompatible"),
            "NBR": _e("conditional", "< 40°C", max_temp=40.0),
        },
    },
    "diesel": {
        "casing": {
            "Cast Iron": _e("recommended"),
            "Carbon Steel": _e("recommended"),
            "SS 316": _e("recommended"),
            "Bronze": _e("recommended"),
        },
        "impeller": {
            "Cast Iron": _e("recommended"),
            "Carbon Steel": _e("recommended"),
            "SS 316": _e("recommended"),
            "Bronze": _e("recommended"),
        },
        "wear_ring": {
            "Cast Iron": _e("recommended"),
            "SS 316": _e("recommended"),
            "Bronze": _e("recommended"),
        },
        "shaft": {
            "Carbon Steel": _e("recommended"),
            "SS 316": _e("recommended"),
        },
        "mechanical_seal": {
            "Carbon/SiC": _e("recommended"),
            "Viton": _e("recommended"),
            "NBR": _e("recommended"),
            "EPDM": _e("incompatible"),
        },
        "o_rings": {
            "Viton": _e("recommended"),
            "NBR": _e("recommended"),
            "EPDM": _e("incompatible"),
            "PTFE": _e("recommended"),
        },
    },
}

COMPONENTS = ["casing", "impeller", "wear_ring", "shaft", "mechanical_seal", "o_rings"]


def _evaluate_rating(entry: _MaterialEntry, temp_c: float, concentration_pct: float) -> MaterialRating:
    """Evaluate a material entry against actual operating conditions."""
    # If already incompatible, stay incompatible
    if entry.rating == "incompatible":
        return MaterialRating(material="", rating="incompatible", note=entry.note)

    # Check temperature limit
    if entry.max_temp_c is not None and temp_c > entry.max_temp_c:
        return MaterialRating(
            material="",
            rating="incompatible",
            note=f"Incompatible above {entry.max_temp_c}°C (operating at {temp_c}°C)",
        )

    # Check concentration limits
    if entry.max_conc_pct is not None and concentration_pct > entry.max_conc_pct:
        return MaterialRating(
            material="",
            rating="incompatible",
            note=f"Incompatible above {entry.max_conc_pct}% concentration (operating at {concentration_pct}%)",
        )
    if entry.min_conc_pct is not None and concentration_pct < entry.min_conc_pct:
        return MaterialRating(
            material="",
            rating="incompatible",
            note=f"Incompatible below {entry.min_conc_pct}% concentration (operating at {concentration_pct}%)",
        )

    return MaterialRating(material="", rating=entry.rating, note=entry.note)


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
        materials = []
        for mat_name, entry in comp_data.items():
            evaluated = _evaluate_rating(entry, temp_c, concentration_pct)
            materials.append(MaterialRating(
                material=mat_name,
                rating=evaluated.rating,
                note=evaluated.note,
            ))
        result.append(ComponentRecommendation(component=component, materials=materials))
    return result
```

- [ ] **Step 4: Run all material selection tests**

Run: `cd apps/api && python -m pytest tests/test_material_selection.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/services/material_selection.py apps/api/tests/test_material_selection.py
git commit -m "feat: add temperature/concentration filtering to material selection (safety-critical)"
```

---

## Chunk 3: Frontend — Pressure Unit Selector + Fluid Presets

### Task 5: Add Pressure Unit Selector to NPSHForm

**Files:**
- Modify: `apps/web/components/calc/NPSHForm.tsx`
- Modify: `apps/web/lib/api.ts` (check if fluid-properties call needed)

- [ ] **Step 1: Add unit conversion helper and fluid preset to NPSHForm**

In `apps/web/components/calc/NPSHForm.tsx`, refactor the component to add:

1. A pressure unit dropdown (kPa, bar, psi, kgf/cm², MPa)
2. A fluid preset dropdown (Water, Diesel, Seawater, Custom)
3. A temperature input that auto-fills vapor pressure and density from the API

```tsx
"use client"
import { useState } from "react"
import { toast } from "sonner"
import { api, ApiError } from "@/lib/api"
import { CalcInput, CalcSelect, CalcLabel, CalcHint, CalcError, CalcEmptyState } from "@/components/ui/calc-form"
import { CalcCard } from "@/components/ui/calc-card"

interface NPSHResult {
  npsha_m: number
  npshr_m: number | null
  safety_margin_m: number | null
  cavitation_risk: boolean
  formula: string
}

interface FormState {
  p_atm: string
  p_vapor: string
  z_s_m: string
  h_loss_m: string
  fluid_density_kg_m3: string
  npshr_m: string
}

type PressureUnit = "kPa" | "bar" | "psi" | "kgf/cm2" | "MPa"

const PRESSURE_UNITS: { value: PressureUnit; label: string }[] = [
  { value: "kPa", label: "kPa" },
  { value: "bar", label: "bar" },
  { value: "psi", label: "psi" },
  { value: "kgf/cm2", label: "kgf/cm²" },
  { value: "MPa", label: "MPa" },
]

// Conversion factors TO kPa
const TO_KPA: Record<PressureUnit, number> = {
  "kPa": 1,
  "bar": 100,
  "psi": 6.89476,
  "kgf/cm2": 98.0665,
  "MPa": 1000,
}

// Default atmospheric pressure in each unit
const ATM_DEFAULTS: Record<PressureUnit, string> = {
  "kPa": "101.325",
  "bar": "1.01325",
  "psi": "14.696",
  "kgf/cm2": "1.0332",
  "MPa": "0.101325",
}

const FLUID_PRESETS = [
  { value: "", label: "Custom (manual input)" },
  { value: "water", label: "Water" },
  { value: "seawater", label: "Seawater" },
  { value: "diesel", label: "Diesel" },
]

function toKpa(value: number, unit: PressureUnit): number {
  return value * TO_KPA[unit]
}

export function NPSHForm() {
  const [loading, setLoading] = useState(false)
  const [loadingFluid, setLoadingFluid] = useState(false)
  const [result, setResult] = useState<NPSHResult | null>(null)
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({})
  const [pressureUnit, setPressureUnit] = useState<PressureUnit>("kPa")
  const [fluidPreset, setFluidPreset] = useState("")
  const [fluidTemp, setFluidTemp] = useState("20")
  const [form, setForm] = useState<FormState>({
    p_atm: "101.325",
    p_vapor: "2.338",
    z_s_m: "5",
    h_loss_m: "2",
    fluid_density_kg_m3: "998.2",
    npshr_m: "",
  })

  function set(key: keyof FormState, value: string) {
    setForm(prev => ({ ...prev, [key]: value }))
    setErrors(prev => ({ ...prev, [key]: undefined }))
    setResult(null)
  }

  function handleUnitChange(unit: PressureUnit) {
    setPressureUnit(unit)
    setForm(prev => ({
      ...prev,
      p_atm: ATM_DEFAULTS[unit],
    }))
    setResult(null)
  }

  async function handleFluidPreset(fluid: string) {
    setFluidPreset(fluid)
    setResult(null)
    if (!fluid) return

    const t = Number(fluidTemp)
    if (Number.isNaN(t)) return

    setLoadingFluid(true)
    try {
      const data = await api.fluidProperties({ fluid, temp_c: t }) as {
        density_kg_m3: number
        vapor_pressure_kpa: number
      }
      // Convert vapor pressure from kPa to current unit
      const vpInUnit = data.vapor_pressure_kpa / TO_KPA[pressureUnit]
      setForm(prev => ({
        ...prev,
        p_vapor: vpInUnit.toFixed(4),
        fluid_density_kg_m3: data.density_kg_m3.toFixed(1),
      }))
    } catch {
      toast.error("Failed to load fluid properties")
    } finally {
      setLoadingFluid(false)
    }
  }

  async function handleTempChange(temp: string) {
    setFluidTemp(temp)
    if (fluidPreset && !Number.isNaN(Number(temp))) {
      await handleFluidPreset(fluidPreset)
    }
  }

  function validate(): boolean {
    const next: Partial<Record<keyof FormState, string>> = {}
    const required: (keyof FormState)[] = ["p_atm", "p_vapor", "z_s_m", "h_loss_m", "fluid_density_kg_m3"]
    for (const key of required) {
      const v = form[key].trim()
      if (!v) { next[key] = "Required"; continue }
      const n = Number(v)
      if (Number.isNaN(n)) next[key] = "Enter a number"
    }
    if (form.npshr_m.trim()) {
      const n = Number(form.npshr_m)
      if (Number.isNaN(n)) next.npshr_m = "Enter a number or leave empty"
    }
    setErrors(next)
    return Object.keys(next).length === 0
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    setResult(null)
    try {
      const body: Record<string, number> = {
        p_atm_kpa: toKpa(Number(form.p_atm), pressureUnit),
        p_vapor_kpa: toKpa(Number(form.p_vapor), pressureUnit),
        z_s_m: Number(form.z_s_m),
        h_loss_m: Number(form.h_loss_m),
        fluid_density_kg_m3: Number(form.fluid_density_kg_m3),
      }
      if (form.npshr_m) {
        body.npshr_m = Number(form.npshr_m)
      }
      const data = await api.npsh(body) as NPSHResult
      setResult(data)
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        toast.error("Monthly calculation limit reached. Upgrade to Pro for unlimited access.")
      } else if (err instanceof ApiError) {
        toast.error(err.message)
      } else {
        toast.error("Calculation failed. Please try again.")
      }
    } finally {
      setLoading(false)
    }
  }

  const unitLabel = PRESSURE_UNITS.find(u => u.value === pressureUnit)?.label ?? pressureUnit

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="space-y-4">
        {/* Pressure Unit Selector */}
        <div className="space-y-1">
          <CalcLabel htmlFor="pressure-unit">Pressure Unit</CalcLabel>
          <CalcSelect
            id="pressure-unit"
            value={pressureUnit}
            onChange={e => handleUnitChange(e.target.value as PressureUnit)}
          >
            {PRESSURE_UNITS.map(u => (
              <option key={u.value} value={u.value}>{u.label}</option>
            ))}
          </CalcSelect>
        </div>

        {/* Fluid Preset */}
        <div className="space-y-1">
          <CalcLabel htmlFor="fluid-preset">Fluid (optional preset)</CalcLabel>
          <div className="grid grid-cols-2 gap-2">
            <CalcSelect
              id="fluid-preset"
              value={fluidPreset}
              onChange={e => handleFluidPreset(e.target.value)}
            >
              {FLUID_PRESETS.map(f => (
                <option key={f.value} value={f.value}>{f.label}</option>
              ))}
            </CalcSelect>
            {fluidPreset && (
              <div className="space-y-1">
                <CalcInput
                  id="fluid-temp"
                  type="text"
                  inputMode="decimal"
                  placeholder="Temperature °C"
                  value={fluidTemp}
                  onChange={e => handleTempChange(e.target.value)}
                />
              </div>
            )}
          </div>
          {loadingFluid && (
            <CalcHint>Loading fluid properties...</CalcHint>
          )}
        </div>

        {/* Atmospheric Pressure */}
        <div className="space-y-1">
          <CalcLabel htmlFor="p_atm">Atmospheric Pressure ({unitLabel})</CalcLabel>
          <CalcInput
            id="p_atm"
            type="text"
            inputMode="decimal"
            placeholder={ATM_DEFAULTS[pressureUnit]}
            value={form.p_atm}
            onChange={e => set("p_atm", e.target.value)}
            aria-invalid={errors.p_atm ? "true" : undefined}
          />
          {errors.p_atm && <CalcError id="p_atm-error">{errors.p_atm}</CalcError>}
          {!errors.p_atm && <CalcHint>Absolute pressure at fluid surface</CalcHint>}
        </div>

        {/* Vapor Pressure */}
        <div className="space-y-1">
          <CalcLabel htmlFor="p_vapor">Vapor Pressure ({unitLabel})</CalcLabel>
          <CalcInput
            id="p_vapor"
            type="text"
            inputMode="decimal"
            placeholder="2.338"
            value={form.p_vapor}
            onChange={e => set("p_vapor", e.target.value)}
            aria-invalid={errors.p_vapor ? "true" : undefined}
          />
          {errors.p_vapor && <CalcError id="p_vapor-error">{errors.p_vapor}</CalcError>}
          {!errors.p_vapor && <CalcHint>Fluid vapor pressure at operating temperature</CalcHint>}
        </div>

        {/* Suction Head */}
        <div className="space-y-1">
          <CalcLabel htmlFor="z_s_m">Suction Head (m)</CalcLabel>
          <CalcInput
            id="z_s_m"
            type="text"
            inputMode="decimal"
            placeholder="5.0"
            value={form.z_s_m}
            onChange={e => set("z_s_m", e.target.value)}
            aria-invalid={errors.z_s_m ? "true" : undefined}
          />
          {errors.z_s_m && <CalcError id="z_s_m-error">{errors.z_s_m}</CalcError>}
          {!errors.z_s_m && <CalcHint>Positive: fluid above pump, Negative: fluid below pump</CalcHint>}
        </div>

        {/* Suction Line Losses */}
        <div className="space-y-1">
          <CalcLabel htmlFor="h_loss_m">Suction Line Losses (m)</CalcLabel>
          <CalcInput
            id="h_loss_m"
            type="text"
            inputMode="decimal"
            placeholder="2.0"
            value={form.h_loss_m}
            onChange={e => set("h_loss_m", e.target.value)}
            aria-invalid={errors.h_loss_m ? "true" : undefined}
          />
          {errors.h_loss_m && <CalcError id="h_loss_m-error">{errors.h_loss_m}</CalcError>}
          {!errors.h_loss_m && <CalcHint>Total friction losses in suction piping</CalcHint>}
        </div>

        {/* Fluid Density */}
        <div className="space-y-1">
          <CalcLabel htmlFor="fluid_density_kg_m3">Fluid Density (kg/m³)</CalcLabel>
          <CalcInput
            id="fluid_density_kg_m3"
            type="text"
            inputMode="decimal"
            placeholder="998.2"
            value={form.fluid_density_kg_m3}
            onChange={e => set("fluid_density_kg_m3", e.target.value)}
            aria-invalid={errors.fluid_density_kg_m3 ? "true" : undefined}
          />
          {errors.fluid_density_kg_m3 && <CalcError id="fluid_density_kg_m3-error">{errors.fluid_density_kg_m3}</CalcError>}
          {!errors.fluid_density_kg_m3 && <CalcHint>Water at 20°C = 998.2 kg/m³</CalcHint>}
        </div>

        {/* NPSHr */}
        <div className="space-y-1">
          <CalcLabel htmlFor="npshr_m">NPSHr from pump curve (m)</CalcLabel>
          <CalcInput
            id="npshr_m"
            type="text"
            inputMode="decimal"
            placeholder="Optional"
            value={form.npshr_m}
            onChange={e => set("npshr_m", e.target.value)}
            aria-invalid={errors.npshr_m ? "true" : undefined}
          />
          {errors.npshr_m && <CalcError id="npshr_m-error">{errors.npshr_m}</CalcError>}
          {!errors.npshr_m && <CalcHint>Required NPSH from manufacturer's pump curve</CalcHint>}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full h-12 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium transition-colors flex items-center justify-center gap-2"
          aria-busy={loading}
        >
          {loading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" aria-hidden />
              Calculating…
            </>
          ) : "Calculate NPSHa"}
        </button>
      </form>

      {!result && (
        <CalcEmptyState>Fill in the fields and calculate to see the result</CalcEmptyState>
      )}

      {result && (
        <CalcCard className="space-y-3 animate-in fade-in-0 slide-in-from-bottom-2 duration-200">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-white">NPSHa Result</h3>
            {result.cavitation_risk ? (
              <span className="px-2 py-1 rounded text-xs font-medium bg-red-900/50 text-red-400 border border-red-500/30">
                CAVITATION RISK
              </span>
            ) : (
              <span className="px-2 py-1 rounded text-xs font-medium bg-green-900/50 text-green-400 border border-green-500/30">
                Safe
              </span>
            )}
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-bold text-white">{result.npsha_m.toFixed(2)}</span>
            <span className="text-lg text-white/60">m</span>
          </div>
          {result.safety_margin_m !== null && (
            <p className="text-sm text-white/60">
              Safety margin:{" "}
              <span className={result.safety_margin_m < 0 ? "text-red-400" : "text-green-400"}>
                {result.safety_margin_m > 0 ? "+" : ""}{result.safety_margin_m} m
              </span>
            </p>
          )}
          <details className="text-xs text-white/40 cursor-pointer">
            <summary className="hover:text-white/60 transition-colors">Show formula</summary>
            <pre className="mt-2 whitespace-pre-wrap font-mono text-[11px] leading-relaxed">
              {result.formula}
            </pre>
          </details>
        </CalcCard>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Add `fluidProperties` method to API client**

Check `apps/web/lib/api.ts` and add:
```typescript
async fluidProperties(body: { fluid: string; temp_c: number }) {
  return this.post("/calculations/fluid-properties", body)
}
```

- [ ] **Step 3: Verify the form renders and unit conversion works**

Run: `cd apps/web && npm run build`
Expected: Build succeeds without errors

- [ ] **Step 4: Commit**

```bash
git add apps/web/components/calc/NPSHForm.tsx apps/web/lib/api.ts
git commit -m "feat: add pressure unit selector and fluid presets to NPSHa form"
```

### Task 6: Improve Material Selection Notes Visibility

**Files:**
- Modify: `apps/web/components/calc/MaterialSelectionForm.tsx:125-136`

- [ ] **Step 1: Update material rendering to show notes prominently**

In `MaterialSelectionForm.tsx`, update the material rendering section (lines 125-136) to show notes more prominently, especially for incompatible materials:

Replace the material row `div` with:
```tsx
<div key={m.material} className="flex items-start justify-between p-3 gap-3">
  <div className="flex-1 min-w-0">
    <p className="text-sm text-white">{m.material}</p>
    {m.note && (
      <p className={`text-xs mt-0.5 ${
        m.rating === "incompatible"
          ? "text-red-400/80"
          : m.rating === "conditional"
            ? "text-yellow-400/80"
            : "text-white/40"
      }`}>
        {m.note}
      </p>
    )}
  </div>
  <span className={`text-xs px-2 py-0.5 rounded-full border font-medium capitalize shrink-0 ${RATING_STYLE[m.rating] ?? ""}`}>
    {m.rating}
  </span>
</div>
```

- [ ] **Step 2: Verify build**

Run: `cd apps/web && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add apps/web/components/calc/MaterialSelectionForm.tsx
git commit -m "feat: improve material selection notes visibility with color-coded warnings"
```

---

## Chunk 4: Run All Tests + Final Verification

### Task 7: Run Full Test Suite

- [ ] **Step 1: Run all backend tests**

Run: `cd apps/api && python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 2: Run frontend build**

Run: `cd apps/web && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Fix any failures found**

If tests fail, fix them and re-run.

- [ ] **Step 4: Final commit if any fixes**

```bash
git add -A
git commit -m "fix: resolve test/build issues from v2 improvements"
```
