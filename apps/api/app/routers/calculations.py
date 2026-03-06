from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.units import convert_unit, ConversionError
from app.services.npsh import calculate_npsha

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
        raise HTTPException(status_code=400, detail=str(e))


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
