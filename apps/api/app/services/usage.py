from datetime import datetime, timezone
from app.core.auth import AUTH_DISABLED
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
    start_of_month = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    result = (
        supabase.table("usage_events")
        .select("*", count="exact")
        .eq("user_id", user_id)
        .eq("event_type", event_type)
        .gte("created_at", start_of_month.isoformat())
        .execute()
    )
    if result.count is not None:
        return int(result.count)
    return len(result.data)


def check_and_record_usage(user_id: str, event_type: str) -> None:
    """Raise ValueError if over limit, else record the event."""
    if AUTH_DISABLED:
        return
    plan = get_user_plan(user_id)
    limit = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"]).get(event_type)
    if limit is not None:
        current = count_monthly_usage(user_id, event_type)
        if current >= limit:
            raise ValueError(
                f"Monthly {event_type} limit ({limit}) reached for {plan} plan"
            )
    supabase = get_supabase()
    supabase.table("usage_events").insert(
        {"user_id": user_id, "event_type": event_type}
    ).execute()
