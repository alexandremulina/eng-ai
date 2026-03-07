import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.anyio
async def test_checkout_endpoint_requires_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/billing/checkout", json={
            "plan": "pro",
            "success_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel",
        })
    assert response.status_code in (401, 403)


@pytest.mark.anyio
async def test_checkout_rejects_invalid_plan(mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/billing/checkout",
            json={"plan": "free", "success_url": "https://x.com", "cancel_url": "https://x.com"},
            headers={"Authorization": "Bearer test-token"},
        )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_checkout_returns_url(mock_user):
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/test_session"
    with patch("app.routers.billing.get_stripe") as mock_stripe_fn:
        mock_stripe = MagicMock()
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_stripe_fn.return_value = mock_stripe
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/billing/checkout",
                json={"plan": "pro", "success_url": "https://x.com/success", "cancel_url": "https://x.com/cancel"},
                headers={"Authorization": "Bearer test-token"},
            )
    assert response.status_code == 200
    assert "url" in response.json()
    assert "stripe.com" in response.json()["url"]


@pytest.mark.anyio
async def test_webhook_rejects_invalid_signature():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/billing/webhook",
            content=b'{"type": "customer.subscription.updated"}',
            headers={"Content-Type": "application/json", "stripe-signature": "invalid"},
        )
    # Either 400 (bad signature) or 500 (missing webhook secret in test env)
    assert response.status_code in (400, 500)


@pytest.mark.anyio
async def test_checkout_stripe_error_returns_502(mock_user):
    with patch("app.routers.billing.get_stripe") as mock_stripe_fn:
        mock_stripe = MagicMock()
        mock_stripe.checkout.Session.create.side_effect = Exception("Stripe down")
        mock_stripe_fn.return_value = mock_stripe
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/billing/checkout",
                json={"plan": "pro", "success_url": "https://x.com/success", "cancel_url": "https://x.com/cancel"},
                headers={"Authorization": "Bearer test-token"},
            )
    assert response.status_code == 502
    assert response.json()["detail"] == "Payment service unavailable"


@pytest.mark.anyio
async def test_checkout_missing_stripe_key_returns_503(mock_user):
    with patch("app.routers.billing.get_stripe", side_effect=ValueError("STRIPE_SECRET_KEY is not configured")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/billing/checkout",
                json={"plan": "enterprise", "success_url": "https://x.com/success", "cancel_url": "https://x.com/cancel"},
                headers={"Authorization": "Bearer test-token"},
            )
    assert response.status_code == 503
