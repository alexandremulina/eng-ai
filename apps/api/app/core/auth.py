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
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
