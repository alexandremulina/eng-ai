from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.supabase import get_supabase

# TODO: set back to False when login is ready
AUTH_DISABLED = True

security = HTTPBearer(auto_error=not AUTH_DISABLED)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
) -> dict:
    """Validate Supabase JWT and return user dict."""
    if AUTH_DISABLED:
        return {"id": "anonymous", "email": "test@engbrain.app"}

    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

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
