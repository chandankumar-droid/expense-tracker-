"""
Router-level tests for the /expenses endpoints.

Uses FastAPI's TestClient with dependency overrides so the real Supabase client
is never called — the service receives a FakeExpenseRepository instead.
"""

from datetime import date, datetime, timezone
from unittest.mock import MagicMock
import uuid

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_expense_service
from app.features.expenses.exceptions import ExpenseNotFoundError
from app.features.expenses.schemas import (
    ExpenseCreate,
    ExpenseListResponse,
    ExpenseResponse,
    ExpenseSummary,
    CategoryBreakdown,
)
from app.features.expenses.service import ExpenseService
from app.main import app
from tests.conftest import FakeExpenseRepository


# ---------------------------------------------------------------------------
# Helper: build a TestClient that uses the FakeExpenseRepository
# ---------------------------------------------------------------------------

def make_client() -> tuple[TestClient, FakeExpenseRepository]:
    """Return a TestClient wired to a fresh FakeExpenseRepository."""
    fake_repo = FakeExpenseRepository()
    fake_service = ExpenseService(repository=fake_repo)

    app.dependency_overrides[get_expense_service] = lambda: fake_service
    client = TestClient(app)
    return client, fake_repo


@pytest.fixture(autouse=True)
def clear_overrides():
    """Ensure dependency overrides are reset after every test."""
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /expenses
# ---------------------------------------------------------------------------

class TestCreateExpense:
    def test_creates_expense_and_returns_201(self) -> None:
        client, _ = make_client()
        payload = {
            "title": "Coffee",
            "amount": 3.50,
            "category": "Food",
            "date": "2024-06-15",
        }
        response = client.post("/expenses", json=payload)
        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Coffee"
        assert body["amount"] == 3.50
        assert body["category"] == "Food"
        assert body["date"] == "2024-06-15"
        assert "id" in body

    def test_returns_422_for_negative_amount(self) -> None:
        client, _ = make_client()
        payload = {"title": "Bad", "amount": -5.0, "category": "Food", "date": "2024-06-01"}
        response = client.post("/expenses", json=payload)
        assert response.status_code == 422

    def test_returns_422_when_title_missing(self) -> None:
        client, _ = make_client()
        response = client.post("/expenses", json={"amount": 10, "category": "Food", "date": "2024-06-01"})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /expenses
# ---------------------------------------------------------------------------

class TestListExpenses:
    def _seed(self, client: TestClient) -> None:
        expenses = [
            {"title": "Coffee", "amount": 3.0, "category": "Food", "date": "2024-06-01"},
            {"title": "Taxi", "amount": 8.0, "category": "Travel", "date": "2024-06-05"},
            {"title": "Lunch", "amount": 12.0, "category": "Food", "date": "2024-06-10"},
        ]
        for e in expenses:
            client.post("/expenses", json=e)

    def test_returns_all_expenses(self) -> None:
        client, _ = make_client()
        self._seed(client)
        response = client.get("/expenses")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 3

    def test_filter_by_category(self) -> None:
        client, _ = make_client()
        self._seed(client)
        response = client.get("/expenses?category=Food")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2

    def test_filter_by_date_range(self) -> None:
        client, _ = make_client()
        self._seed(client)
        response = client.get("/expenses?date_from=2024-06-01&date_to=2024-06-05")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2

    def test_pagination_response_shape(self) -> None:
        client, _ = make_client()
        self._seed(client)
        response = client.get("/expenses?page=1&page_size=2")
        assert response.status_code == 200
        body = response.json()
        assert len(body["items"]) == 2
        assert body["total_pages"] == 2

    def test_returns_422_for_invalid_date_range(self) -> None:
        client, _ = make_client()
        response = client.get("/expenses?date_from=2024-06-30&date_to=2024-06-01")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /expenses/summary
# ---------------------------------------------------------------------------

class TestGetSummary:
    def test_returns_summary_for_month(self) -> None:
        client, _ = make_client()
        expenses = [
            {"title": "Coffee", "amount": 5.0, "category": "Food", "date": "2024-06-01"},
            {"title": "Taxi", "amount": 10.0, "category": "Travel", "date": "2024-06-15"},
        ]
        for e in expenses:
            client.post("/expenses", json=e)

        response = client.get("/expenses/summary?month=6&year=2024")
        assert response.status_code == 200
        body = response.json()
        assert body["month"] == 6
        assert body["year"] == 2024
        assert body["total_spending"] == 15.0
        assert body["expense_count"] == 2
        assert len(body["breakdown"]) == 2

    def test_returns_422_for_invalid_month(self) -> None:
        client, _ = make_client()
        response = client.get("/expenses/summary?month=13&year=2024")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /expenses/{id}
# ---------------------------------------------------------------------------

class TestGetExpenseById:
    def test_returns_expense_when_found(self) -> None:
        client, _ = make_client()
        created = client.post(
            "/expenses",
            json={"title": "Book", "amount": 20.0, "category": "Education", "date": "2024-06-01"},
        ).json()

        response = client.get(f"/expenses/{created['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_returns_404_for_missing_id(self) -> None:
        client, _ = make_client()
        response = client.get(f"/expenses/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_returns_404_for_invalid_uuid(self) -> None:
        client, _ = make_client()
        response = client.get("/expenses/not-a-uuid")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /expenses/{id}
# ---------------------------------------------------------------------------

class TestDeleteExpense:
    def test_deletes_expense_and_returns_204(self) -> None:
        client, _ = make_client()
        created = client.post(
            "/expenses",
            json={"title": "Snack", "amount": 2.0, "category": "Food", "date": "2024-06-01"},
        ).json()

        response = client.delete(f"/expenses/{created['id']}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/expenses/{created['id']}")
        assert get_response.status_code == 404

    def test_returns_404_for_missing_expense(self) -> None:
        client, _ = make_client()
        response = client.delete(f"/expenses/{uuid.uuid4()}")
        assert response.status_code == 404
