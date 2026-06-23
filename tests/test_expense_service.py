"""
Unit tests for ExpenseService.

Uses FakeExpenseRepository (defined in conftest.py) — no real database connection needed.
Each test gets a fresh repository and a fresh service instance.
"""

from datetime import date
import uuid

import pytest

from app.features.expenses.exceptions import ExpenseNotFoundError, InvalidDateRangeError
from app.features.expenses.schemas import ExpenseCreate
from app.features.expenses.service import ExpenseService
from tests.conftest import FakeExpenseRepository


@pytest.fixture
def service(fake_repo: FakeExpenseRepository) -> ExpenseService:
    return ExpenseService(repository=fake_repo)


# ---------------------------------------------------------------------------
# create_expense
# ---------------------------------------------------------------------------

class TestCreateExpense:
    def test_returns_created_expense(self, service: ExpenseService) -> None:
        data = ExpenseCreate(
            title="Coffee",
            amount=3.50,
            category="Food",
            date=date(2024, 6, 15),
        )
        result = service.create_expense(data)

        assert result.title == "Coffee"
        assert result.amount == 3.50
        assert result.category == "Food"
        assert result.date == date(2024, 6, 15)
        assert result.description is None
        assert result.id is not None

    def test_creates_expense_with_description(self, service: ExpenseService) -> None:
        data = ExpenseCreate(
            title="Flight",
            amount=250.00,
            category="Travel",
            date=date(2024, 6, 1),
            description="Business trip to Mumbai",
        )
        result = service.create_expense(data)
        assert result.description == "Business trip to Mumbai"


# ---------------------------------------------------------------------------
# get_expense
# ---------------------------------------------------------------------------

class TestGetExpense:
    def test_returns_expense_when_found(self, service: ExpenseService) -> None:
        created = service.create_expense(
            ExpenseCreate(title="Lunch", amount=10.0, category="Food", date=date(2024, 5, 1))
        )
        result = service.get_expense(str(created.id))
        assert result.id == created.id
        assert result.title == "Lunch"

    def test_raises_not_found_when_missing(self, service: ExpenseService) -> None:
        missing_id = str(uuid.uuid4())
        with pytest.raises(ExpenseNotFoundError) as exc_info:
            service.get_expense(missing_id)
        assert missing_id in str(exc_info.value)

    def test_raises_not_found_for_invalid_uuid(self, service: ExpenseService) -> None:
        with pytest.raises(ExpenseNotFoundError):
            service.get_expense("not-a-uuid")


# ---------------------------------------------------------------------------
# list_expenses
# ---------------------------------------------------------------------------

class TestListExpenses:
    def _seed(self, service: ExpenseService) -> None:
        """Seed the repo with a mix of categories and dates."""
        expenses = [
            ExpenseCreate(title="Coffee", amount=3.0, category="Food", date=date(2024, 6, 1)),
            ExpenseCreate(title="Lunch", amount=12.0, category="Food", date=date(2024, 6, 10)),
            ExpenseCreate(title="Taxi", amount=8.0, category="Travel", date=date(2024, 6, 5)),
            ExpenseCreate(title="Book", amount=15.0, category="Education", date=date(2024, 7, 1)),
        ]
        for e in expenses:
            service.create_expense(e)

    def test_returns_all_when_no_filters(self, service: ExpenseService) -> None:
        self._seed(service)
        result = service.list_expenses(None, None, None, page=1, page_size=10)
        assert result.total == 4

    def test_filters_by_category(self, service: ExpenseService) -> None:
        self._seed(service)
        result = service.list_expenses("Food", None, None, page=1, page_size=10)
        assert result.total == 2
        assert all(e.category == "Food" for e in result.items)

    def test_filters_by_date_range(self, service: ExpenseService) -> None:
        self._seed(service)
        result = service.list_expenses(
            None, date(2024, 6, 1), date(2024, 6, 30), page=1, page_size=10
        )
        assert result.total == 3

    def test_pagination_works(self, service: ExpenseService) -> None:
        self._seed(service)
        result = service.list_expenses(None, None, None, page=1, page_size=2)
        assert len(result.items) == 2
        assert result.total == 4
        assert result.total_pages == 2

    def test_raises_invalid_date_range(self, service: ExpenseService) -> None:
        with pytest.raises(InvalidDateRangeError):
            service.list_expenses(None, date(2024, 6, 30), date(2024, 6, 1), page=1, page_size=10)


# ---------------------------------------------------------------------------
# delete_expense
# ---------------------------------------------------------------------------

class TestDeleteExpense:
    def test_deletes_existing_expense(self, service: ExpenseService) -> None:
        created = service.create_expense(
            ExpenseCreate(title="Snack", amount=2.0, category="Food", date=date(2024, 6, 1))
        )
        service.delete_expense(str(created.id))  # should not raise

        with pytest.raises(ExpenseNotFoundError):
            service.get_expense(str(created.id))

    def test_raises_not_found_when_deleting_missing(self, service: ExpenseService) -> None:
        with pytest.raises(ExpenseNotFoundError):
            service.delete_expense(str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# get_summary — the key differentiator
# ---------------------------------------------------------------------------

class TestGetSummary:
    def _seed_june_2024(self, service: ExpenseService) -> None:
        expenses = [
            ExpenseCreate(title="Coffee", amount=3.00, category="Food", date=date(2024, 6, 1)),
            ExpenseCreate(title="Lunch", amount=12.00, category="Food", date=date(2024, 6, 10)),
            ExpenseCreate(title="Taxi", amount=8.00, category="Travel", date=date(2024, 6, 5)),
            # Outside target month — should NOT appear in summary
            ExpenseCreate(title="Book", amount=15.00, category="Education", date=date(2024, 7, 1)),
        ]
        for e in expenses:
            service.create_expense(e)

    def test_total_spending_is_correct(self, service: ExpenseService) -> None:
        self._seed_june_2024(service)
        summary = service.get_summary(month=6, year=2024)
        assert summary.total_spending == 23.00

    def test_expense_count_excludes_other_months(self, service: ExpenseService) -> None:
        self._seed_june_2024(service)
        summary = service.get_summary(month=6, year=2024)
        assert summary.expense_count == 3  # July expense excluded

    def test_breakdown_has_correct_categories(self, service: ExpenseService) -> None:
        self._seed_june_2024(service)
        summary = service.get_summary(month=6, year=2024)
        categories = {b.category for b in summary.breakdown}
        assert categories == {"Food", "Travel"}

    def test_breakdown_category_totals_correct(self, service: ExpenseService) -> None:
        self._seed_june_2024(service)
        summary = service.get_summary(month=6, year=2024)
        food = next(b for b in summary.breakdown if b.category == "Food")
        travel = next(b for b in summary.breakdown if b.category == "Travel")
        assert food.total == 15.00
        assert food.count == 2
        assert travel.total == 8.00
        assert travel.count == 1

    def test_summary_empty_month(self, service: ExpenseService) -> None:
        summary = service.get_summary(month=1, year=2020)
        assert summary.total_spending == 0.0
        assert summary.expense_count == 0
        assert summary.breakdown == []
