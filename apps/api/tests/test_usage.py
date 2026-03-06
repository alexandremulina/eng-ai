import pytest
from unittest.mock import patch, MagicMock
from app.services.usage import (
    get_user_plan,
    count_monthly_usage,
    check_and_record_usage,
    PLAN_LIMITS,
)


# Override the autouse mock_usage fixture so it doesn't interfere with
# the unit tests in this file that patch usage internals directly.
@pytest.fixture(autouse=True)
def mock_usage():
    yield


def test_get_user_plan_defaults_to_free():
    with patch("app.services.usage.get_supabase") as mock_sb:
        mock_sb.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        result = get_user_plan("user-123")
    assert result == "free"


def test_get_user_plan_returns_stored_plan():
    with patch("app.services.usage.get_supabase") as mock_sb:
        mock_sb.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"plan": "pro"}
        ]
        result = get_user_plan("user-123")
    assert result == "pro"


def test_check_and_record_usage_within_limit():
    with patch("app.services.usage.get_supabase") as mock_sb, patch(
        "app.services.usage.get_user_plan", return_value="free"
    ), patch("app.services.usage.count_monthly_usage", return_value=5):
        mock_sb.return_value.table.return_value.insert.return_value.execute.return_value = (
            MagicMock()
        )
        # Should not raise
        check_and_record_usage("user-123", "calculation")


def test_check_and_record_usage_at_limit_raises():
    with patch("app.services.usage.get_user_plan", return_value="free"), patch(
        "app.services.usage.count_monthly_usage", return_value=50
    ):  # at limit
        with pytest.raises(ValueError, match="limit"):
            check_and_record_usage("user-123", "calculation")


def test_pro_plan_has_no_limits():
    with patch("app.services.usage.get_user_plan", return_value="pro"), patch(
        "app.services.usage.get_supabase"
    ) as mock_sb:
        mock_sb.return_value.table.return_value.insert.return_value.execute.return_value = (
            MagicMock()
        )
        # Should not raise regardless of usage count
        check_and_record_usage("user-123", "calculation")


def test_plan_limits_structure():
    assert PLAN_LIMITS["free"]["calculation"] == 50
    assert PLAN_LIMITS["free"]["ai_query"] == 10
    assert PLAN_LIMITS["free"]["diagnosis"] == 5
    assert PLAN_LIMITS["pro"]["calculation"] is None
    assert PLAN_LIMITS["enterprise"]["ai_query"] is None


def test_count_monthly_usage():
    with patch("app.services.usage.get_supabase") as mock_sb:
        (
            mock_sb.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.gte.return_value.execute.return_value.count
        ) = 7
        result = count_monthly_usage("user-123", "calculation")
    assert result == 7


def test_count_monthly_usage_returns_zero_when_none():
    with patch("app.services.usage.get_supabase") as mock_sb:
        mock_result = mock_sb.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.gte.return_value.execute.return_value
        mock_result.count = None
        mock_result.data = []
        result = count_monthly_usage("user-123", "calculation")
    assert result == 0


def test_count_monthly_usage_returns_int():
    with patch("app.services.usage.get_supabase") as mock_sb:
        mock_sb.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.gte.return_value.execute.return_value.count = 7
        result = count_monthly_usage("user-123", "calculation")
    assert isinstance(result, int)
    assert result == 7


def test_count_monthly_usage_falls_back_to_len_data_when_count_none():
    with patch("app.services.usage.get_supabase") as mock_sb:
        mock_result = mock_sb.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.gte.return_value.execute.return_value
        mock_result.count = None
        mock_result.data = [{"id": 1}, {"id": 2}, {"id": 3}]
        result = count_monthly_usage("user-123", "calculation")
    assert result == 3
