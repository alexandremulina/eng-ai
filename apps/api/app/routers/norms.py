from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.core.auth import get_current_user
from app.services.rag import query_norms
from app.services.usage import check_and_record_usage

router = APIRouter(prefix="/norms", tags=["norms"])


class NormQueryRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=2000)
    language: str = Field(default="en", pattern="^(en|pt|es)$")


@router.post("/query")
async def query(req: NormQueryRequest, user: dict = Depends(get_current_user)):
    try:
        check_and_record_usage(user["id"], "ai_query")
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))
    try:
        result = await query_norms(req.question, user["id"], req.language)
        return result
    except ValueError as e:
        # Config error (missing API key, etc.)
        raise HTTPException(status_code=500, detail=f"Service configuration error: {e}")
    except Exception:
        raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
