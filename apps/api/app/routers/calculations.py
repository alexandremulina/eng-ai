from __future__ import annotations

import base64
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from app.services.units import convert_unit, ConversionError
from app.services.npsh import calculate_npsha
from app.services.head_loss import calculate_head_loss
from app.services.usage import check_and_record_usage
from app.services.bolt_torque import calculate_bolt_torque
from app.core.auth import get_current_user
from app.services.ai import call_vision_llm
from app.services.parallel_pumps import (
    calculate_parallel_pumps,
    PumpCurvePoint as SvcPumpCurvePoint,
    SystemCurve as SvcSystemCurve,
    PumpInput as SvcPumpInput,
)
from app.services.material_selection import select_materials

router = APIRouter(prefix="/calculations", tags=["calculations"])


class ConvertRequest(BaseModel):
    value: float
    from_unit: str
    to_unit: str
    decimals: int = Field(default=4, ge=0, le=15)


class ConvertResponse(BaseModel):
    value: float
    from_unit: str
    to_unit: str
    result: float


@router.post("/convert", response_model=ConvertResponse)
async def convert(req: ConvertRequest, user: dict = Depends(get_current_user)):
    try:
        result = convert_unit(req.value, req.from_unit, req.to_unit, req.decimals)
        return ConvertResponse(
            value=req.value,
            from_unit=req.from_unit,
            to_unit=req.to_unit,
            result=result,
        )
    except ConversionError as e:
        raise HTTPException(status_code=400, detail=str(e))


class NPSHRequest(BaseModel):
    p_atm_kpa: float = Field(..., gt=0, description="Absolute pressure at fluid surface (kPa)")
    p_vapor_kpa: float = Field(..., ge=0, description="Fluid vapor pressure at operating temperature (kPa)")
    z_s_m: float = Field(..., description="Suction head (m) — positive if fluid above pump")
    h_loss_m: float = Field(..., ge=0, description="Total friction losses in suction piping (m)")
    fluid_density_kg_m3: float = Field(..., gt=0, description="Fluid density (kg/m³)")
    g: float = Field(default=9.81, gt=0, description="Gravitational acceleration (m/s²)")
    npshr_m: float | None = Field(default=None, gt=0, description="Required NPSH from pump curve (m)")


@router.post("/npsh")
async def npsh(req: NPSHRequest, user: dict = Depends(get_current_user)):
    try:
        check_and_record_usage(user["id"], "calculation")
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))
    try:
        result = calculate_npsha(**req.model_dump())
        return {
            "npsha_m": result.npsha_m,
            "npshr_m": result.npshr_m,
            "safety_margin_m": result.safety_margin_m,
            "cavitation_risk": result.cavitation_risk,
            "formula": result.formula,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class HeadLossRequest(BaseModel):
    flow_m3h: float = Field(..., gt=0, description="Volumetric flow rate (m³/h)")
    pipe_diameter_mm: float = Field(..., gt=0, description="Internal pipe diameter (mm)")
    pipe_length_m: float = Field(..., gt=0, description="Pipe length (m)")
    pipe_roughness_mm: float = Field(default=0.046, ge=0, description="Absolute pipe roughness (mm) — 0.046 = commercial steel")
    fluid_density_kg_m3: float = Field(default=998.2, gt=0, description="Fluid density (kg/m³)")
    fluid_viscosity_cP: float = Field(default=1.002, gt=0, description="Dynamic viscosity (cP)")


@router.post("/head-loss")
async def head_loss(req: HeadLossRequest, user: dict = Depends(get_current_user)):
    try:
        check_and_record_usage(user["id"], "calculation")
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))
    try:
        result = calculate_head_loss(**req.model_dump())
        return {
            "head_loss_m": result.head_loss_m,
            "velocity_m_s": result.velocity_m_s,
            "reynolds_number": result.reynolds_number,
            "friction_factor": result.friction_factor,
            "flow_regime": result.flow_regime,
            "formula": result.formula,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class PumpCurvePointModel(BaseModel):
    q: float = Field(..., ge=0, description="Flow rate (m³/h)")
    h: float = Field(..., ge=0, description="Head (m)")


class PumpInputModel(BaseModel):
    name: str
    points: list[PumpCurvePointModel] = Field(..., min_length=1)
    bep_q: float | None = Field(default=None, gt=0)


class SystemCurveModel(BaseModel):
    static_head: float = Field(..., ge=0, description="Static head (m)")
    resistance: float = Field(..., ge=0, description="System resistance R — H = H_static + R*Q²")


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


class BoltTorqueRequest(BaseModel):
    grade: str
    diameter_mm: float = Field(..., gt=0, le=100)
    condition: str = Field(default="dry")


@router.post("/bolt-torque")
async def bolt_torque(req: BoltTorqueRequest, user: dict = Depends(get_current_user)):
    try:
        check_and_record_usage(user["id"], "calculation")
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))
    try:
        result = calculate_bolt_torque(req.grade, req.diameter_mm, req.condition)
        return {
            "grade": result.grade,
            "diameter_mm": result.diameter_mm,
            "diameter_used_mm": result.diameter_used_mm,
            "condition": result.condition,
            "proof_load_mpa": result.proof_load_mpa,
            "preload_kn": result.preload_kn,
            "torque_nm": result.torque_nm,
            "torque_ftlb": result.torque_ftlb,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class MaterialSelectionRequest(BaseModel):
    fluid: str
    concentration_pct: float = Field(default=100.0, ge=0, le=100)
    temp_c: float = Field(default=25.0)


@router.post("/material-selection")
async def material_selection(req: MaterialSelectionRequest, user: dict = Depends(get_current_user)):
    try:
        check_and_record_usage(user["id"], "calculation")
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))
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


CURVE_EXTRACTION_PROMPT = """You are analyzing a pump performance curve chart.
Extract the H-Q (Head vs Flow) curve data points from this image.
Return ONLY a valid JSON array of objects with "q" (flow, numeric) and "h" (head, numeric) keys.
Extract at least 3 points spanning the full curve range.
Example: [{"q": 0, "h": 45}, {"q": 10, "h": 40}, {"q": 20, "h": 30}, {"q": 30, "h": 15}]
Do not include units, labels, or any text outside the JSON array."""


@router.post("/extract-pump-curve")
async def extract_pump_curve(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    content = await file.read()
    b64 = base64.b64encode(content).decode()
    mime = file.content_type or "image/png"

    try:
        raw = await call_vision_llm(b64, CURVE_EXTRACTION_PROMPT, mime_type=mime)
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        points = json.loads(raw)
        if not isinstance(points, list) or len(points) < 3:
            raise ValueError("Too few points extracted")
        validated = []
        for i, p in enumerate(points):
            if "q" not in p or "h" not in p:
                raise ValueError(f"Point at index {i} missing required field 'q' or 'h'")
            try:
                validated.append({"q": float(p["q"]), "h": float(p["h"])})
            except (TypeError, ValueError):
                raise ValueError(f"Point at index {i}: 'q' and 'h' must be numeric")
        return {"points": validated}
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Could not extract curve: {e}")
