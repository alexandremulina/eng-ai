# EngBrain Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a mobile-first PWA for pump engineers with precision calculation engine, AI norm consulting (RAG), photo failure diagnosis, and SaaS billing.

**Architecture:** Next.js 15 (App Router) frontend as PWA communicates with a FastAPI Python backend for all calculations and AI orchestration. Supabase handles auth, Postgres (with pgvector), and file storage. OpenRouter routes prompts to the best LLM per task.

**Tech Stack:** Next.js 15, Tailwind, shadcn/ui, next-intl, FastAPI, Python 3.12, fluids, scipy, pint, LangChain, Supabase, OpenRouter, Stripe, Railway

---

## Task 1: Monorepo Structure + Tooling

**Files:**
- Create: `package.json` (root, workspaces)
- Create: `apps/web/` (Next.js)
- Create: `apps/api/` (FastAPI)
- Create: `.gitignore`
- Create: `README.md`

**Step 1: Initialize monorepo**

```bash
mkdir -p apps/web apps/api
cat > package.json << 'EOF'
{
  "name": "eng-brain",
  "private": true,
  "workspaces": ["apps/web"]
}
EOF
```

**Step 2: Create Next.js app**

```bash
cd apps/web
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir --import-alias "@/*"
```

**Step 3: Create FastAPI project**

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn pydantic fluids scipy numpy pint langchain langchain-community openai supabase python-dotenv pytest httpx
pip freeze > requirements.txt
```

**Step 4: Create project structure**

```bash
mkdir -p apps/api/app/{routers,services,models,core}
touch apps/api/app/__init__.py
touch apps/api/app/main.py
touch apps/api/app/core/__init__.py
touch apps/api/app/core/config.py
touch apps/api/app/routers/__init__.py
touch apps/api/app/services/__init__.py
touch apps/api/app/models/__init__.py
mkdir -p apps/api/tests
touch apps/api/tests/__init__.py
```

**Step 5: Create root .gitignore**

```
node_modules/
.next/
.env
.env.local
.env*.local
apps/api/.venv/
apps/api/__pycache__/
apps/api/**/__pycache__/
*.pyc
.DS_Store
```

**Step 6: Commit**

```bash
git add .
git commit -m "chore: initialize monorepo with Next.js and FastAPI"
```

---

## Task 2: FastAPI Core Config + Health Check

**Files:**
- Create: `apps/api/app/core/config.py`
- Create: `apps/api/app/main.py`
- Create: `apps/api/.env.example`
- Create: `apps/api/tests/test_health.py`

**Step 1: Write failing test**

```python
# apps/api/tests/test_health.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 2: Run test to verify it fails**

```bash
cd apps/api
pytest tests/test_health.py -v
```
Expected: FAIL — `ModuleNotFoundError` or `ImportError`

**Step 3: Write config**

```python
# apps/api/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openrouter_api_key: str = ""
    supabase_url: str = ""
    supabase_service_key: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    environment: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
```

**Step 4: Write main.py**

```python
# apps/api/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(title="EngBrain API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://engbrain.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Step 5: Install pydantic-settings**

```bash
pip install pydantic-settings
pip freeze > requirements.txt
```

**Step 6: Run test to verify it passes**

```bash
pytest tests/test_health.py -v
```
Expected: PASS

**Step 7: Create .env.example**

```
OPENROUTER_API_KEY=sk-or-...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
ENVIRONMENT=development
```

**Step 8: Commit**

```bash
git add apps/api/
git commit -m "feat: add FastAPI core config and health check"
```

---

## Task 3: Unit Conversion Service (with Precision)

**Files:**
- Create: `apps/api/app/services/units.py`
- Create: `apps/api/app/routers/calculations.py`
- Create: `apps/api/tests/test_units.py`

**Step 1: Write failing tests**

```python
# apps/api/tests/test_units.py
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
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_units.py -v
```
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement unit service**

```python
# apps/api/app/services/units.py
from pint import UnitRegistry, DimensionalityError
from decimal import Decimal

ureg = UnitRegistry()

class ConversionError(Exception):
    pass

# Map friendly aliases to pint units
UNIT_MAP = {
    "gpm": "gallon / minute",
    "m3/h": "meter**3 / hour",
    "m3/s": "meter**3 / second",
    "l/s": "liter / second",
    "psi": "pound_force_per_square_inch",
    "bar": "bar",
    "kPa": "kilopascal",
    "MPa": "megapascal",
    "degC": "degC",
    "degF": "degF",
    "K": "kelvin",
    "m": "meter",
    "mm": "millimeter",
    "inch": "inch",
    "ft": "foot",
    "kg/m3": "kilogram / meter**3",
    "mPa*s": "millipascal * second",
    "cP": "centipoise",
    "kW": "kilowatt",
    "hp": "horsepower",
    "rpm": "revolution / minute",
}

def convert_unit(value: float, from_unit: str, to_unit: str, decimals: int = 6) -> float:
    """Convert value between engineering units with pint precision."""
    try:
        from_pint = UNIT_MAP.get(from_unit, from_unit)
        to_pint = UNIT_MAP.get(to_unit, to_unit)
        quantity = ureg.Quantity(value, from_pint)
        converted = quantity.to(to_pint).magnitude
        return round(float(converted), decimals)
    except DimensionalityError as e:
        raise ConversionError(f"Cannot convert {from_unit} to {to_unit}: incompatible dimensions") from e
    except Exception as e:
        raise ConversionError(f"Conversion error: {e}") from e
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_units.py -v
```
Expected: PASS

**Step 5: Add router**

```python
# apps/api/app/routers/calculations.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.units import convert_unit, ConversionError

router = APIRouter(prefix="/calculations", tags=["calculations"])

class ConvertRequest(BaseModel):
    value: float
    from_unit: str
    to_unit: str
    decimals: int = 4

class ConvertResponse(BaseModel):
    value: float
    from_unit: str
    to_unit: str
    result: float

@router.post("/convert", response_model=ConvertResponse)
async def convert(req: ConvertRequest):
    try:
        result = convert_unit(req.value, req.from_unit, req.to_unit, req.decimals)
        return ConvertResponse(
            value=req.value,
            from_unit=req.from_unit,
            to_unit=req.to_unit,
            result=result,
        )
    except ConversionError as e:
        raise HTTPException(status_code=422, detail=str(e))
```

**Step 6: Register router in main.py**

```python
# apps/api/app/main.py — add after middleware setup
from app.routers import calculations
app.include_router(calculations.router)
```

**Step 7: Commit**

```bash
git add apps/api/
git commit -m "feat: add unit conversion service with pint precision"
```

---

## Task 4: NPSH Calculation Service

**Files:**
- Create: `apps/api/app/services/npsh.py`
- Create: `apps/api/tests/test_npsh.py`
- Modify: `apps/api/app/routers/calculations.py`

**Step 1: Write failing tests**

```python
# apps/api/tests/test_npsh.py
import pytest
from app.services.npsh import calculate_npsha, NPSHResult

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
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_npsh.py -v
```
Expected: FAIL

**Step 3: Implement NPSH service**

```python
# apps/api/app/services/npsh.py
from dataclasses import dataclass

@dataclass
class NPSHResult:
    npsha_m: float          # Available NPSH in meters
    npshr_m: float | None   # Required NPSH (if provided)
    safety_margin_m: float | None
    cavitation_risk: bool
    formula: str            # Human-readable formula used

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
    pressure_head_m = ((p_atm_kpa - p_vapor_kpa) * 1000) / (fluid_density_kg_m3 * g)
    npsha_m = round(pressure_head_m + z_s_m - h_loss_m, 4)

    safety_margin = None
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
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_npsh.py -v
```
Expected: PASS

**Step 5: Add NPSH endpoint to router**

```python
# Append to apps/api/app/routers/calculations.py

from app.services.npsh import calculate_npsha

class NPSHRequest(BaseModel):
    p_atm_kpa: float
    p_vapor_kpa: float
    z_s_m: float
    h_loss_m: float
    fluid_density_kg_m3: float
    g: float = 9.81
    npshr_m: float | None = None

@router.post("/npsh")
async def npsh(req: NPSHRequest):
    result = calculate_npsha(**req.model_dump())
    return {
        "npsha_m": result.npsha_m,
        "npshr_m": result.npshr_m,
        "safety_margin_m": result.safety_margin_m,
        "cavitation_risk": result.cavitation_risk,
        "formula": result.formula,
    }
```

**Step 6: Commit**

```bash
git add apps/api/
git commit -m "feat: add NPSH calculation service with cavitation detection"
```

---

## Task 5: Head Loss Calculation (Darcy-Weisbach)

**Files:**
- Create: `apps/api/app/services/head_loss.py`
- Create: `apps/api/tests/test_head_loss.py`
- Modify: `apps/api/app/routers/calculations.py`

**Step 1: Write failing tests**

```python
# apps/api/tests/test_head_loss.py
import pytest
from app.services.head_loss import calculate_head_loss, HeadLossResult

def test_turbulent_water_steel_pipe():
    """Water at 20°C in 100mm steel pipe, 50 m length, 2 m/s velocity."""
    result = calculate_head_loss(
        flow_m3h=56.5,       # ~2 m/s in 100mm pipe
        pipe_diameter_mm=100.0,
        pipe_length_m=50.0,
        pipe_roughness_mm=0.046,  # commercial steel
        fluid_density_kg_m3=998.2,
        fluid_viscosity_cP=1.002,
    )
    assert result.flow_regime == "turbulent"
    assert 3.0 < result.head_loss_m < 7.0  # typical range

def test_laminar_regime():
    """Viscous fluid, slow flow — should be laminar."""
    result = calculate_head_loss(
        flow_m3h=1.0,
        pipe_diameter_mm=50.0,
        pipe_length_m=10.0,
        pipe_roughness_mm=0.046,
        fluid_density_kg_m3=900.0,
        fluid_viscosity_cP=100.0,  # viscous oil
    )
    assert result.flow_regime == "laminar"
    assert result.reynolds_number < 2300
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_head_loss.py -v
```
Expected: FAIL

**Step 3: Implement head loss service**

```python
# apps/api/app/services/head_loss.py
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
    """
    D = pipe_diameter_mm / 1000.0       # m
    roughness = pipe_roughness_mm / 1000.0  # m
    Q = flow_m3h / 3600.0              # m³/s
    A = math.pi * (D / 2) ** 2         # m²
    v = Q / A                           # m/s
    nu = (fluid_viscosity_cP * 1e-3) / fluid_density_kg_m3  # m²/s

    Re = fluids.Reynolds(V=v, D=D, nu=nu)

    if Re < 2300:
        regime = "laminar"
        f = 64 / Re
    elif Re > 4000:
        regime = "turbulent"
        fd = fluids.friction_factor(Re=Re, eD=roughness / D)
        f = fd
    else:
        regime = "transitional"
        fd = fluids.friction_factor(Re=Re, eD=roughness / D)
        f = fd

    g = 9.81
    h_f = f * (pipe_length_m / D) * (v ** 2 / (2 * g))

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
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_head_loss.py -v
```
Expected: PASS

**Step 5: Add endpoint to router** (append to `calculations.py`)

```python
from app.services.head_loss import calculate_head_loss

class HeadLossRequest(BaseModel):
    flow_m3h: float
    pipe_diameter_mm: float
    pipe_length_m: float
    pipe_roughness_mm: float = 0.046
    fluid_density_kg_m3: float = 998.2
    fluid_viscosity_cP: float = 1.002

@router.post("/head-loss")
async def head_loss(req: HeadLossRequest):
    result = calculate_head_loss(**req.model_dump())
    return {
        "head_loss_m": result.head_loss_m,
        "velocity_m_s": result.velocity_m_s,
        "reynolds_number": result.reynolds_number,
        "friction_factor": result.friction_factor,
        "flow_regime": result.flow_regime,
        "formula": result.formula,
    }
```

**Step 6: Commit**

```bash
git add apps/api/
git commit -m "feat: add Darcy-Weisbach head loss service"
```

---

## Task 6: Supabase Setup + Auth Middleware

**Files:**
- Create: `apps/api/app/core/supabase.py`
- Create: `apps/api/app/core/auth.py`
- Create: `apps/api/tests/test_auth.py`

**Step 1: Install supabase client**

```bash
cd apps/api && pip install supabase
pip freeze > requirements.txt
```

**Step 2: Write supabase client**

```python
# apps/api/app/core/supabase.py
from supabase import create_client, Client
from app.core.config import settings

def get_supabase() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_key)
```

**Step 3: Write auth middleware**

```python
# apps/api/app/core/auth.py
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.supabase import get_supabase

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict:
    """Validate Supabase JWT and return user dict."""
    token = credentials.credentials
    supabase = get_supabase()
    try:
        response = supabase.auth.get_user(token)
        if response.user is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"id": response.user.id, "email": response.user.email}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
```

**Step 4: Write failing test**

```python
# apps/api/tests/test_auth.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_protected_route_without_token_returns_401():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/calculations/npsh", json={
            "p_atm_kpa": 101.325,
            "p_vapor_kpa": 2.338,
            "z_s_m": 5.0,
            "h_loss_m": 2.0,
            "fluid_density_kg_m3": 998.2,
        })
    assert response.status_code == 403  # no auth header = 403 from HTTPBearer
```

**Step 5: Add auth to calculation endpoints** (modify `calculations.py` NPSH endpoint signature)

```python
from app.core.auth import get_current_user
from fastapi import Depends

# Add to each endpoint:
async def npsh(req: NPSHRequest, user: dict = Depends(get_current_user)):
```

**Step 6: Run test to verify it passes**

```bash
pytest tests/test_auth.py -v
```
Expected: PASS

**Step 7: Commit**

```bash
git add apps/api/
git commit -m "feat: add Supabase auth middleware for protected endpoints"
```

---

## Task 7: Usage Tracking (Rate Limiting per Plan)

**Files:**
- Create: `apps/api/app/services/usage.py`
- Create: `apps/api/tests/test_usage.py`

**Step 1: Create Supabase tables** (run in Supabase SQL editor)

```sql
-- User plans
create table user_plans (
  user_id uuid primary key references auth.users(id),
  plan text not null default 'free',  -- 'free' | 'pro' | 'enterprise'
  updated_at timestamptz default now()
);

-- Usage events
create table usage_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id),
  event_type text not null,  -- 'calculation' | 'ai_query' | 'diagnosis'
  created_at timestamptz default now()
);

-- Enable RLS
alter table user_plans enable row level security;
alter table usage_events enable row level security;
```

**Step 2: Write usage service**

```python
# apps/api/app/services/usage.py
from app.core.supabase import get_supabase

PLAN_LIMITS = {
    "free": {"calculation": 50, "ai_query": 10, "diagnosis": 5},
    "pro": {"calculation": None, "ai_query": None, "diagnosis": None},
    "enterprise": {"calculation": None, "ai_query": None, "diagnosis": None},
}

def get_user_plan(user_id: str) -> str:
    supabase = get_supabase()
    result = supabase.table("user_plans").select("plan").eq("user_id", user_id).execute()
    if result.data:
        return result.data[0]["plan"]
    return "free"

def count_monthly_usage(user_id: str, event_type: str) -> int:
    supabase = get_supabase()
    from datetime import datetime, timezone
    start_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    result = (
        supabase.table("usage_events")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .eq("event_type", event_type)
        .gte("created_at", start_of_month.isoformat())
        .execute()
    )
    return result.count or 0

def check_and_record_usage(user_id: str, event_type: str) -> None:
    """Raise ValueError if over limit, else record the event."""
    plan = get_user_plan(user_id)
    limit = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"]).get(event_type)
    if limit is not None:
        current = count_monthly_usage(user_id, event_type)
        if current >= limit:
            raise ValueError(f"Monthly {event_type} limit ({limit}) reached for {plan} plan")
    supabase = get_supabase()
    supabase.table("usage_events").insert({"user_id": user_id, "event_type": event_type}).execute()
```

**Step 3: Wire usage check into protected endpoints**

```python
# In each endpoint that should be tracked, add:
from app.services.usage import check_and_record_usage

async def npsh(req: NPSHRequest, user: dict = Depends(get_current_user)):
    try:
        check_and_record_usage(user["id"], "calculation")
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))
    ...
```

**Step 4: Commit**

```bash
git add apps/api/
git commit -m "feat: add usage tracking and plan-based rate limiting"
```

---

## Task 8: OpenRouter AI Service

**Files:**
- Create: `apps/api/app/services/ai.py`
- Create: `apps/api/tests/test_ai.py`

**Step 1: Write AI service**

```python
# apps/api/app/services/ai.py
import httpx
from app.core.config import settings

MODELS = {
    "reasoning": "deepseek/deepseek-r1",
    "rag": "google/gemini-2.5-pro",
    "vision": "google/gemini-2.5-pro",
    "report": "anthropic/claude-sonnet-4-6",
    "fallback": "meta-llama/llama-3.3-70b-instruct",
}

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

async def call_llm(
    messages: list[dict],
    task: str = "reasoning",
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> str:
    """Call OpenRouter with task-appropriate model."""
    model = MODELS.get(task, MODELS["fallback"])
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "HTTP-Referer": "https://engbrain.app",
        "X-Title": "EngBrain",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(OPENROUTER_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

async def call_vision_llm(image_base64: str, prompt: str) -> str:
    """Call vision-capable model with image."""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                {"type": "text", "text": prompt},
            ],
        }
    ]
    return await call_llm(messages, task="vision", max_tokens=4096)
```

**Step 2: Commit**

```bash
git add apps/api/
git commit -m "feat: add OpenRouter AI service with task-based model routing"
```

---

## Task 9: RAG Norm Consultant

**Files:**
- Create: `apps/api/app/services/rag.py`
- Create: `apps/api/app/routers/norms.py`

**Step 1: Install LangChain + pgvector deps**

```bash
pip install langchain langchain-openai langchain-community pgvector psycopg2-binary pypdf
pip freeze > requirements.txt
```

**Step 2: Implement RAG service**

```python
# apps/api/app/services/rag.py
import json
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from supabase import Client
from app.core.supabase import get_supabase
from app.core.config import settings
from app.services.ai import call_llm

# Use OpenRouter-compatible embeddings endpoint
import openai

def get_embeddings_client():
    return openai.AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
    )

NORM_SYSTEM_PROMPT = """You are a senior pump engineering specialist with deep expertise in:
- API 610 (centrifugal pumps for petroleum industry)
- API 682 (shaft sealing systems)
- ASME B73 (horizontal end-suction pumps)
- ISO 5199 (technical specifications for centrifugal pumps)

Answer the engineer's question using ONLY the provided context from the norm documents.
Always cite: norm name, section number, and page if available.
If the context doesn't contain the answer, say so explicitly — never guess.
Format your response clearly with the citation at the end."""

async def query_norms(question: str, user_id: str, language: str = "en") -> dict:
    """RAG query against norm documents."""
    supabase = get_supabase()

    # Get embedding for the question
    client = get_embeddings_client()
    embedding_response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=question,
    )
    question_embedding = embedding_response.data[0].embedding

    # Search Supabase pgvector
    results = supabase.rpc(
        "match_norm_documents",
        {
            "query_embedding": question_embedding,
            "match_threshold": 0.7,
            "match_count": 5,
            "filter_user_id": user_id,
        },
    ).execute()

    if not results.data:
        return {"answer": "No relevant norm sections found for this query.", "citations": []}

    context_chunks = [r["content"] for r in results.data]
    citations = [{"source": r["metadata"].get("source", "Unknown"), "page": r["metadata"].get("page")} for r in results.data]
    context = "\n\n---\n\n".join(context_chunks)

    messages = [
        {"role": "system", "content": NORM_SYSTEM_PROMPT},
        {"role": "user", "content": f"Context from norm documents:\n\n{context}\n\nQuestion: {question}"},
    ]

    answer = await call_llm(messages, task="rag", temperature=0.0)
    return {"answer": answer, "citations": citations}
```

**Step 3: Create Supabase SQL function for vector search** (run in Supabase SQL editor)

```sql
-- Enable pgvector
create extension if not exists vector;

-- Norm documents table
create table norm_documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id),  -- null = public norm
  content text not null,
  embedding vector(1536),
  metadata jsonb default '{}',
  created_at timestamptz default now()
);

-- Vector search function
create or replace function match_norm_documents(
  query_embedding vector(1536),
  match_threshold float,
  match_count int,
  filter_user_id uuid
)
returns table (id uuid, content text, metadata jsonb, similarity float)
language plpgsql
as $$
begin
  return query
  select
    nd.id, nd.content, nd.metadata,
    1 - (nd.embedding <=> query_embedding) as similarity
  from norm_documents nd
  where
    (nd.user_id is null or nd.user_id = filter_user_id)
    and 1 - (nd.embedding <=> query_embedding) > match_threshold
  order by nd.embedding <=> query_embedding
  limit match_count;
end;
$$;
```

**Step 4: Add norms router**

```python
# apps/api/app/routers/norms.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.auth import get_current_user
from app.services.rag import query_norms
from app.services.usage import check_and_record_usage

router = APIRouter(prefix="/norms", tags=["norms"])

class NormQueryRequest(BaseModel):
    question: str
    language: str = "en"

@router.post("/query")
async def query(req: NormQueryRequest, user: dict = Depends(get_current_user)):
    try:
        check_and_record_usage(user["id"], "ai_query")
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))
    result = await query_norms(req.question, user["id"], req.language)
    return result
```

**Step 5: Register router in main.py**

```python
from app.routers import norms
app.include_router(norms.router)
```

**Step 6: Commit**

```bash
git add apps/api/
git commit -m "feat: add RAG norm consultant with pgvector and OpenRouter"
```

---

## Task 10: Photo Diagnosis Endpoint

**Files:**
- Create: `apps/api/app/services/diagnosis.py`
- Create: `apps/api/app/routers/diagnosis.py`

**Step 1: Implement diagnosis service**

```python
# apps/api/app/services/diagnosis.py
import base64
import json
from app.services.ai import call_vision_llm

DIAGNOSIS_SYSTEM = """You are a pump failure analysis expert trained on ISO 14224 failure taxonomy.
Analyze the provided image of a pump component and return a JSON object with:
{
  "component": "identified component (e.g., mechanical seal, impeller, bearing)",
  "root_cause": "most likely cause of failure or condition",
  "severity": "low | medium | high | critical",
  "confidence": "low | medium | high",
  "immediate_action": "what to do right now",
  "preventive_action": "how to prevent recurrence",
  "possible_causes": ["list", "of", "other", "possible", "causes"],
  "disclaimer": "This is an AI-assisted diagnosis. Always validate with certified inspection."
}
Respond ONLY with valid JSON. No markdown, no extra text."""

async def diagnose_component(image_bytes: bytes, notes: str = "") -> dict:
    """Analyze pump component image for failure diagnosis."""
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    prompt = DIAGNOSIS_SYSTEM
    if notes:
        prompt += f"\n\nEngineer notes: {notes}"

    raw = await call_vision_llm(image_b64, prompt)

    # Strip markdown code blocks if present
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        return {
            "component": "Unknown",
            "root_cause": "Could not parse AI response",
            "severity": "unknown",
            "confidence": "low",
            "immediate_action": "Manual inspection required",
            "preventive_action": "N/A",
            "possible_causes": [],
            "disclaimer": "AI diagnosis unavailable. Raw response: " + raw[:200],
        }
```

**Step 2: Add diagnosis router**

```python
# apps/api/app/routers/diagnosis.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from app.core.auth import get_current_user
from app.services.diagnosis import diagnose_component
from app.services.usage import check_and_record_usage

router = APIRouter(prefix="/diagnosis", tags=["diagnosis"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    notes: str = Form(default=""),
    user: dict = Depends(get_current_user),
):
    try:
        check_and_record_usage(user["id"], "diagnosis")
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))

    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=422, detail="Only JPEG, PNG, or WebP images accepted")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Image too large (max 10MB)")

    result = await diagnose_component(contents, notes)
    return result
```

**Step 3: Register router in main.py**

```python
from app.routers import diagnosis
app.include_router(diagnosis.router)
```

**Step 4: Commit**

```bash
git add apps/api/
git commit -m "feat: add photo diagnosis endpoint with vision LLM"
```

---

## Task 11: Next.js Frontend Setup

**Files:**
- Modify: `apps/web/tailwind.config.ts`
- Create: `apps/web/lib/api.ts`
- Create: `apps/web/middleware.ts`

**Step 1: Install dependencies**

```bash
cd apps/web
npx shadcn@latest init
npx shadcn@latest add button card input label tabs sheet sonner badge
npm install @supabase/supabase-js @supabase/ssr next-intl next-themes zustand
```

**Step 2: Configure dark theme in tailwind**

```ts
// apps/web/tailwind.config.ts
import type { Config } from "tailwindcss"
const config: Config = {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: "#0066FF", foreground: "#ffffff" },
        success: { DEFAULT: "#00C853" },
        surface: { DEFAULT: "#0F1117", secondary: "#1A1D27" },
      },
    },
  },
  plugins: [],
}
export default config
```

**Step 3: Create API client**

```ts
// apps/web/lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

async function apiFetch<T>(
  path: string,
  options: RequestInit & { token?: string } = {}
): Promise<T> {
  const { token, ...fetchOptions } = options
  const res = await fetch(`${API_URL}${path}`, {
    ...fetchOptions,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...fetchOptions.headers,
    },
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail ?? "Request failed")
  }
  return res.json()
}

export const api = {
  convert: (body: object, token: string) =>
    apiFetch("/calculations/convert", { method: "POST", body: JSON.stringify(body), token }),
  npsh: (body: object, token: string) =>
    apiFetch("/calculations/npsh", { method: "POST", body: JSON.stringify(body), token }),
  headLoss: (body: object, token: string) =>
    apiFetch("/calculations/head-loss", { method: "POST", body: JSON.stringify(body), token }),
  queryNorms: (body: object, token: string) =>
    apiFetch("/norms/query", { method: "POST", body: JSON.stringify(body), token }),
  diagnose: (formData: FormData, token: string) =>
    apiFetch("/diagnosis/analyze", { method: "POST", body: formData, token,
      headers: { Authorization: `Bearer ${token}` } }),
}
```

**Step 4: Set up Supabase client**

```ts
// apps/web/lib/supabase.ts
import { createBrowserClient } from "@supabase/ssr"

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
```

**Step 5: Create .env.local.example**

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

**Step 6: Commit**

```bash
git add apps/web/
git commit -m "feat: setup Next.js frontend with shadcn, Supabase, and API client"
```

---

## Task 12: App Layout + Theme

**Files:**
- Modify: `apps/web/app/layout.tsx`
- Create: `apps/web/app/globals.css`
- Create: `apps/web/components/nav/BottomNav.tsx`
- Create: `apps/web/components/ThemeProvider.tsx`

**Step 1: Configure global layout with dark default**

```tsx
// apps/web/app/layout.tsx
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/ThemeProvider"
import { Toaster } from "@/components/ui/sonner"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "EngBrain",
  description: "Engineering tools for pump specialists",
  manifest: "/manifest.json",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} bg-surface text-white`}>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          {children}
          <Toaster richColors />
        </ThemeProvider>
      </body>
    </html>
  )
}
```

**Step 2: Create BottomNav**

```tsx
// apps/web/components/nav/BottomNav.tsx
"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Calculator, BookOpen, Camera, User } from "lucide-react"
import { cn } from "@/lib/utils"

const NAV_ITEMS = [
  { href: "/calc", label: "Calc", icon: Calculator },
  { href: "/norms", label: "Norms", icon: BookOpen },
  { href: "/diagnosis", label: "Diagnosis", icon: Camera },
  { href: "/account", label: "Account", icon: User },
]

export function BottomNav() {
  const pathname = usePathname()
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-surface-secondary border-t border-white/10 pb-safe">
      <div className="flex items-center justify-around h-16">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex flex-col items-center gap-1 text-xs px-4 py-2 rounded-lg transition-colors",
              pathname.startsWith(href)
                ? "text-brand"
                : "text-white/50 hover:text-white/80"
            )}
          >
            <Icon size={22} />
            <span>{label}</span>
          </Link>
        ))}
      </div>
    </nav>
  )
}
```

**Step 3: Install lucide-react**

```bash
npm install lucide-react
```

**Step 4: Commit**

```bash
git add apps/web/
git commit -m "feat: add app layout with dark theme and bottom navigation"
```

---

## Task 13: NPSH Calculator Page

**Files:**
- Create: `apps/web/app/(app)/calc/page.tsx`
- Create: `apps/web/app/(app)/calc/npsh/page.tsx`
- Create: `apps/web/components/calc/NPSHForm.tsx`

**Step 1: Create NPSH form component**

```tsx
// apps/web/components/calc/NPSHForm.tsx
"use client"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import { api } from "@/lib/api"
import { useSession } from "@/lib/useSession"

interface NPSHResult {
  npsha_m: number
  npshr_m: number | null
  safety_margin_m: number | null
  cavitation_risk: boolean
  formula: string
}

export function NPSHForm() {
  const { token } = useSession()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<NPSHResult | null>(null)
  const [form, setForm] = useState({
    p_atm_kpa: "101.325",
    p_vapor_kpa: "2.338",
    z_s_m: "5",
    h_loss_m: "2",
    fluid_density_kg_m3: "998.2",
    npshr_m: "",
  })

  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }))

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!token) return toast.error("Please log in")
    setLoading(true)
    try {
      const body = {
        p_atm_kpa: Number(form.p_atm_kpa),
        p_vapor_kpa: Number(form.p_vapor_kpa),
        z_s_m: Number(form.z_s_m),
        h_loss_m: Number(form.h_loss_m),
        fluid_density_kg_m3: Number(form.fluid_density_kg_m3),
        ...(form.npshr_m ? { npshr_m: Number(form.npshr_m) } : {}),
      }
      const data = await api.npsh(body, token) as NPSHResult
      setResult(data)
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Calculation failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={onSubmit} className="space-y-4">
        {[
          { key: "p_atm_kpa", label: "Atmospheric Pressure (kPa)", placeholder: "101.325" },
          { key: "p_vapor_kpa", label: "Vapor Pressure (kPa)", placeholder: "2.338" },
          { key: "z_s_m", label: "Suction Head (m)", placeholder: "5.0" },
          { key: "h_loss_m", label: "Suction Line Losses (m)", placeholder: "2.0" },
          { key: "fluid_density_kg_m3", label: "Fluid Density (kg/m³)", placeholder: "998.2" },
          { key: "npshr_m", label: "NPSHr from pump curve (m) — optional", placeholder: "leave empty if unknown" },
        ].map(({ key, label, placeholder }) => (
          <div key={key} className="space-y-1">
            <Label htmlFor={key}>{label}</Label>
            <Input
              id={key}
              inputMode="decimal"
              placeholder={placeholder}
              value={form[key as keyof typeof form]}
              onChange={e => set(key, e.target.value)}
              className="text-lg h-12"
            />
          </div>
        ))}
        <Button type="submit" className="w-full h-12 text-base" disabled={loading}>
          {loading ? "Calculating..." : "Calculate NPSHa"}
        </Button>
      </form>

      {result && (
        <Card className="bg-surface-secondary border-white/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              NPSHa Result
              {result.cavitation_risk ? (
                <Badge variant="destructive">CAVITATION RISK</Badge>
              ) : (
                <Badge className="bg-success text-black">Safe</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-4xl font-bold text-brand">{result.npsha_m} m</div>
            {result.safety_margin_m !== null && (
              <p className="text-sm text-white/70">
                Safety margin: <span className={result.safety_margin_m < 0 ? "text-red-400" : "text-success"}>{result.safety_margin_m} m</span>
              </p>
            )}
            <details className="text-xs text-white/50 mt-2">
              <summary className="cursor-pointer">Show formula</summary>
              <pre className="mt-1 whitespace-pre-wrap">{result.formula}</pre>
            </details>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
```

**Step 2: Create calc index and NPSH pages**

```tsx
// apps/web/app/(app)/calc/page.tsx
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const CALCULATORS = [
  { href: "/calc/npsh", title: "NPSH Calculator", desc: "Net Positive Suction Head — cavitation prevention" },
  { href: "/calc/head-loss", title: "Head Loss", desc: "Darcy-Weisbach friction losses" },
  { href: "/calc/convert", title: "Unit Converter", desc: "GPM, bar, kPa, m³/h and more" },
]

export default function CalcPage() {
  return (
    <div className="p-4 space-y-3 pb-20">
      <h1 className="text-xl font-bold">Calculators</h1>
      {CALCULATORS.map(c => (
        <Link key={c.href} href={c.href}>
          <Card className="bg-surface-secondary border-white/10 hover:border-brand transition-colors cursor-pointer">
            <CardHeader className="pb-1"><CardTitle className="text-base">{c.title}</CardTitle></CardHeader>
            <CardContent><p className="text-sm text-white/60">{c.desc}</p></CardContent>
          </Card>
        </Link>
      ))}
    </div>
  )
}
```

```tsx
// apps/web/app/(app)/calc/npsh/page.tsx
import { NPSHForm } from "@/components/calc/NPSHForm"

export default function NPSHPage() {
  return (
    <div className="p-4 pb-20">
      <h1 className="text-xl font-bold mb-4">NPSH Calculator</h1>
      <NPSHForm />
    </div>
  )
}
```

**Step 3: Commit**

```bash
git add apps/web/
git commit -m "feat: add NPSH calculator UI"
```

---

## Task 14: Stripe SaaS Integration

**Files:**
- Create: `apps/api/app/routers/billing.py`
- Create: `apps/web/app/(app)/account/page.tsx`

**Step 1: Install Stripe**

```bash
cd apps/api && pip install stripe
pip freeze > requirements.txt
cd ../web && npm install @stripe/stripe-js
```

**Step 2: Add billing router**

```python
# apps/api/app/routers/billing.py
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.config import settings
from app.core.auth import get_current_user
from app.core.supabase import get_supabase

stripe.api_key = settings.stripe_secret_key
router = APIRouter(prefix="/billing", tags=["billing"])

PRICE_IDS = {
    "pro": "price_xxx_pro_monthly",
    "enterprise": "price_xxx_enterprise_monthly",
}

@router.post("/checkout")
async def create_checkout(plan: str, user: dict = Depends(get_current_user)):
    if plan not in PRICE_IDS:
        raise HTTPException(status_code=422, detail="Invalid plan")
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        client_reference_id=user["id"],
        customer_email=user["email"],
        line_items=[{"price": PRICE_IDS[plan], "quantity": 1}],
        success_url="https://engbrain.app/account?success=1",
        cancel_url="https://engbrain.app/account",
        subscription_data={"trial_period_days": 14},
    )
    return {"url": session.url}

@router.post("/webhook")
async def webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "customer.subscription.updated":
        sub = event["data"]["object"]
        user_id = sub["metadata"].get("user_id") or sub.get("client_reference_id")
        plan = "pro" if sub["status"] == "active" else "free"
        supabase = get_supabase()
        supabase.table("user_plans").upsert({"user_id": user_id, "plan": plan}).execute()

    return {"received": True}
```

**Step 3: Register router in main.py**

```python
from app.routers import billing
app.include_router(billing.router)
```

**Step 4: Commit**

```bash
git add apps/api/ apps/web/
git commit -m "feat: add Stripe billing with checkout and webhook"
```

---

## Task 15: PWA Manifest + Service Worker

**Files:**
- Create: `apps/web/public/manifest.json`
- Modify: `apps/web/next.config.ts`

**Step 1: Install next-pwa**

```bash
cd apps/web && npm install next-pwa
```

**Step 2: Create manifest**

```json
// apps/web/public/manifest.json
{
  "name": "EngBrain",
  "short_name": "EngBrain",
  "description": "Engineering tools for pump specialists",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0F1117",
  "theme_color": "#0066FF",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

**Step 3: Configure next-pwa**

```ts
// apps/web/next.config.ts
import withPWA from "next-pwa"

const pwaConfig = withPWA({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  runtimeCaching: [
    {
      urlPattern: /^https:\/\/.*\.supabase\.co\/.*/i,
      handler: "NetworkFirst",
    },
  ],
})

export default pwaConfig({})
```

**Step 4: Commit**

```bash
git add apps/web/
git commit -m "feat: add PWA manifest and service worker for offline support"
```

---

## Task 16: i18n Setup

**Files:**
- Create: `apps/web/i18n/en.json`
- Create: `apps/web/i18n/pt.json`
- Create: `apps/web/i18n/es.json`
- Create: `apps/web/i18n/request.ts`

**Step 1: Configure next-intl**

```ts
// apps/web/i18n/request.ts
import { getRequestConfig } from "next-intl/server"
import { cookies } from "next/headers"

export default getRequestConfig(async () => {
  const cookieStore = await cookies()
  const locale = cookieStore.get("locale")?.value ?? "en"
  const messages = (await import(`./${locale}.json`)).default
  return { locale, messages }
})
```

**Step 2: Create translation files**

```json
// apps/web/i18n/en.json
{
  "nav": { "calc": "Calc", "norms": "Norms", "diagnosis": "Diagnosis", "account": "Account" },
  "calc": {
    "npsh": { "title": "NPSH Calculator", "result": "NPSHa Result", "safe": "Safe", "risk": "Cavitation Risk" }
  }
}
```

```json
// apps/web/i18n/pt.json
{
  "nav": { "calc": "Cálculo", "norms": "Normas", "diagnosis": "Diagnóstico", "account": "Conta" },
  "calc": {
    "npsh": { "title": "Calculadora NPSH", "result": "Resultado NPSHd", "safe": "Seguro", "risk": "Risco de Cavitação" }
  }
}
```

```json
// apps/web/i18n/es.json
{
  "nav": { "calc": "Cálculo", "norms": "Normas", "diagnosis": "Diagnóstico", "account": "Cuenta" },
  "calc": {
    "npsh": { "title": "Calculadora NPSH", "result": "Resultado NPSHd", "safe": "Seguro", "risk": "Riesgo de Cavitación" }
  }
}
```

**Step 3: Commit**

```bash
git add apps/web/
git commit -m "feat: add i18n with PT/EN/ES translations"
```

---

## Task 17: Railway Deploy (API) + Vercel Deploy (Web)

**Files:**
- Create: `apps/api/Procfile`
- Create: `apps/api/railway.toml`

**Step 1: Create Railway config**

```toml
# apps/api/railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 10
```

**Step 2: Set Railway environment variables** (via Railway dashboard)
- `OPENROUTER_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `ENVIRONMENT=production`

**Step 3: Deploy web to Vercel**

```bash
cd apps/web
npx vercel --prod
```

Set Vercel env vars:
- `NEXT_PUBLIC_API_URL` → Railway URL
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

**Step 4: Final commit**

```bash
git add .
git commit -m "chore: add deployment config for Railway and Vercel"
```

---

## Running Locally

```bash
# Terminal 1 — API
cd apps/api
source .venv/bin/activate
cp .env.example .env  # fill in values
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Web
cd apps/web
cp .env.local.example .env.local  # fill in values
npm run dev
```

API docs: http://localhost:8000/docs
Web: http://localhost:3000
