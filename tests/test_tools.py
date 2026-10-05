"""Deterministic math/business-logic tests for the service layer - the
exact calculations the project's core principle says must come from
SQL/Python, never guessed by the LLM.

Requires the dev stack running, seeded via app/db/init.sql (ground truth:
user 1 = 3480 EUR total, 2420 EUR/4 transactions in electronics; user 2 =
3000 EUR total, a single electronics transaction). Reads real data via the
real DB - faking exact-number correctness would defeat the point.
"""
import pytest

from app.core.current_user import set_current_user_id
from app.services.transactions import (
    calculate_category_spending,
    compare_category_to_total,
    get_current_user_total_spending,
    import_transactions_csv,
    list_current_user_categories,
    list_current_user_transactions,
    resolve_category,
)


@pytest.fixture(autouse=True)
def _as_demo1():
    set_current_user_id(1)


def test_calculate_category_spending_electronics():
    result = calculate_category_spending("electronics")
    assert result == {
        "total": 2420.0,
        "currency": "EUR",
        "category": "electronics",
        "transaction_count": 4,
    }


def test_calculate_category_spending_restaurant():
    result = calculate_category_spending("restaurant")
    assert result["total"] == 230.0
    assert result["transaction_count"] == 3


def test_get_current_user_total_spending():
    assert get_current_user_total_spending() == {"EUR": 3480.0}


def test_compare_category_to_total():
    result = compare_category_to_total("electronics")
    assert result["category_total"] == 2420.0
    assert result["overall_total"] == 3480.0
    assert result["percentage"] == pytest.approx(2420 / 3480 * 100, abs=0.1)


def test_resolve_category_is_case_and_plural_insensitive():
    assert resolve_category("Electronics") == "electronics"
    assert resolve_category("restaurants") == "restaurant"


def test_resolve_category_unknown_raises_with_valid_list():
    with pytest.raises(ValueError, match="Unknown category 'shoes'"):
        resolve_category("shoes")


def test_list_current_user_categories():
    assert set(list_current_user_categories()) == {
        "electronics", "groceries", "restaurant", "sport", "travel",
    }


def test_list_current_user_transactions_no_filter_returns_all():
    assert len(list_current_user_transactions()) == 11


def test_list_current_user_transactions_filtered():
    rows = list_current_user_transactions("sport")
    assert len(rows) == 1
    assert rows[0]["merchant"] == "Swimming Pool"


def test_different_users_see_different_totals():
    set_current_user_id(2)
    assert get_current_user_total_spending() == {"EUR": 3000.0}


# --- CSV import parsing/validation (DB write mocked - this only tests the
# parsing/validation logic, not persistence, which app/api/transactions.py's
# own tests cover) ---

def test_import_transactions_csv_validates_rows(monkeypatch):
    import app.services.transactions as txn_service

    captured = []
    monkeypatch.setattr(
        txn_service, "import_current_user_transactions", lambda rows: captured.extend(rows)
    )

    csv_text = (
        "merchant,amount,currency,category,transaction_date\n"
        "Coffee Shop,5.50,EUR,restaurant,2026-09-01\n"
        "BadAmount,-1,EUR,restaurant,2026-09-02\n"
        "BadCurrency,5,E,restaurant,2026-09-03\n"
    )

    result = txn_service.import_transactions_csv(csv_text)

    assert result["imported"] == 1
    assert result["skipped"] == 2
    assert len(result["errors"]) == 2
    assert len(captured) == 1
    assert captured[0]["merchant"] == "Coffee Shop"
