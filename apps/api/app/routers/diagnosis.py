from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from app.core.auth import get_current_user
from app.services.diagnosis import diagnose_component
from app.services.usage import check_and_record_usage

router = APIRouter(prefix="/diagnosis", tags=["diagnosis"])

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
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

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type: {file.content_type}. Use JPEG, PNG, or WebP.",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Image too large (max 10MB)")

    try:
        result = await diagnose_component(contents, notes, mime_type=file.content_type)
        return result
    except Exception:
        raise HTTPException(status_code=503, detail="Diagnosis service temporarily unavailable")
