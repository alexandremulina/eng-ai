import pytest
from unittest.mock import patch
from app.core.auth import get_current_user
from app.main import app

TEST_USER = {"id": "test-user-id", "email": "test@test.com"}


@pytest.fixture
def mock_user():
    """Override get_current_user dependency for tests that need it."""
    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    yield TEST_USER
    del app.dependency_overrides[get_current_user]


@pytest.fixture(autouse=True)
def mock_usage():
    """Auto-mock usage tracking for all tests (avoids real Supabase calls)."""
    with patch("app.services.usage.get_user_plan", return_value="pro"), \
         patch("app.services.usage.count_monthly_usage", return_value=0), \
         patch("app.services.usage.get_supabase"):
        yield
