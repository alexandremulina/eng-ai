import pytest
from app.core.auth import get_current_user
from app.main import app

TEST_USER = {"id": "test-user-id", "email": "test@test.com"}


@pytest.fixture
def mock_user():
    """Override get_current_user dependency for tests that need it."""
    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    yield TEST_USER
    del app.dependency_overrides[get_current_user]
