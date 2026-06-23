"""
Shared fixtures and the FakeExpenseRepository used across all tests.

FakeExpenseRepository is an in-memory implementation of AbstractExpenseRepository.
- No real database connection required.
- Service tests use this directly.
- Router tests use it via FastAPI dependency overrides.
"""

from calendar import monthrange
from datetime import date, datetime, timezone
from typing import Optional
import uuid

import pytest

from app.features.expenses.models import Expense
from app.features.expenses.repository import AbstractExpenseRepository


class FakeExpenseRepository(AbstractExpenseRepository):
    """In-memory repository — implements the same interface as SupabaseExpenseRepository."""

    def __init__(self) -> None:
        self._store: list[Expense] = []

    def create(
        self,
        title: str,
        amount: float,
        category: str,
        expense_date: date,
        description: Optional[str],
    ) -> Expense:
        expense = Expense(
            id=uuid.uuid4(),
            title=title,
            amount=amount,
            category=category,
            date=expense_date,
            description=description,
            created_at=datetime.now(tz=timezone.utc),
        )
        self._store.append(expense)
        return expense

    def get_by_id(self, expense_id: uuid.UUID) -> Optional[Expense]:
        return next((e for e in self._store if e.id == expense_id), None)

    def list(
        self,
        category: Optional[str],
        date_from: Optional[date],
        date_to: Optional[date],
        offset: int,
        limit: int,
    ) -> tuple[list[Expense], int]:
        results = self._store[:]

        if category:
            results = [e for e in results if e.category == category]
        if date_from:
            results = [e for e in results if e.date >= date_from]
        if date_to:
            results = [e for e in results if e.date <= date_to]

        total = len(results)
        page_items = results[offset: offset + limit]
        return page_items, total

    def delete(self, expense_id: uuid.UUID) -> bool:
        for i, e in enumerate(self._store):
            if e.id == expense_id:
                self._store.pop(i)
                return True
        return False

    def get_by_month(self, month: int, year: int) -> list[Expense]:
        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])
        return [e for e in self._store if first_day <= e.date <= last_day]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_repo() -> FakeExpenseRepository:
    """Fresh in-memory repository for each test."""
    return FakeExpenseRepository()
