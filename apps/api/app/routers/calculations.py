from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.units import convert_unit, ConversionError

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
