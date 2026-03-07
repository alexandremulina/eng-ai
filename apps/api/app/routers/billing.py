from __future__ import annotations
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from app.core.config import get_settings
from app.core.auth import get_current_user
from app.core.supabase import get_supabase

router = APIRouter(prefix="/billing", tags=["billing"])

VALID_PLANS = {"pro", "enterprise"}

PRICE_IDS = {
    "pro": "price_pro_placeholder",       # Replace with real Stripe price ID
    "enterprise": "price_enterprise_placeholder",
}


def get_stripe():
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise ValueError("STRIPE_SECRET_KEY is not configured")
    stripe.api_key = settings.stripe_secret_key
    return stripe


class CheckoutRequest(BaseModel):
    plan: str = Field(..., pattern="^(pro|enterprise)$")
    success_url: str = Field(..., min_length=1)
    cancel_url: str = Field(..., min_length=1)


@router.post("/checkout")
async def create_checkout(req: CheckoutRequest, user: dict = Depends(get_current_user)):
    try:
        s = get_stripe()
        session = s.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            client_reference_id=user["id"],
            customer_email=user["email"],
            line_items=[{"price": PRICE_IDS[req.plan], "quantity": 1}],
            success_url=req.success_url,
            cancel_url=req.cancel_url,
            subscription_data={"trial_period_days": 14},
        )
        return {"url": session.url}
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Payment service unavailable")


@router.post("/webhook")
async def webhook(request: Request):
    settings = get_settings()
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    try:
        s = get_stripe()
        event = s.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    if event["type"] in ("customer.subscription.updated", "customer.subscription.created"):
        sub = event["data"]["object"]
        user_id = sub.get("client_reference_id") or sub.get("metadata", {}).get("user_id")
        if user_id:
            plan = "free"
            if sub.get("status") == "active":
                items = sub.get("items", {}).get("data", [])
                if items:
                    price_id = items[0].get("price", {}).get("id", "")
                    if price_id == PRICE_IDS.get("enterprise"):
                        plan = "enterprise"
                    elif price_id == PRICE_IDS.get("pro"):
                        plan = "pro"
            supabase = get_supabase()
            supabase.table("user_plans").upsert({"user_id": user_id, "plan": plan}).execute()

    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        user_id = sub.get("client_reference_id") or sub.get("metadata", {}).get("user_id")
        if user_id:
            supabase = get_supabase()
            supabase.table("user_plans").upsert({"user_id": user_id, "plan": "free"}).execute()

    return {"received": True}
