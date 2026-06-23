from collections import defaultdict
from datetime import date
from typing import Optional
import uuid

from app.features.expenses.exceptions import ExpenseNotFoundError, InvalidDateRangeError
from app.features.expenses.models import Expense
from app.features.expenses.repository import AbstractExpenseRepository
from app.features.expenses.schemas import (
    CategoryBreakdown,
    ExpenseCreate,
    ExpenseListResponse,
    ExpenseResponse,
    ExpenseSummary,
)


def _expense_to_response(expense: Expense) -> ExpenseResponse:
    """Map internal domain model → API response schema."""
    return ExpenseResponse(
        id=expense.id,
        title=expense.title,
        amount=expense.amount,
        category=expense.category,
        date=expense.date,
        description=expense.description,
        created_at=expense.created_at,
    )


class ExpenseService:
    """
    Business logic layer.

    - Receives the repository via constructor injection — never imports the DB client.
    - Raises domain exceptions (ExpenseNotFoundError, etc.) — never HTTPException.
    - Summary / aggregation logic lives here, not in the router or repository.
    """

    def __init__(self, repository: AbstractExpenseRepository) -> None:
        self._repo = repository

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_expense(self, data: ExpenseCreate) -> ExpenseResponse:
        expense = self._repo.create(
            title=data.title,
            amount=data.amount,
            category=data.category,
            expense_date=data.date,
            description=data.description,
        )
        return _expense_to_response(expense)

    # ------------------------------------------------------------------
    # Get by ID
    # ------------------------------------------------------------------

    def get_expense(self, expense_id: str) -> ExpenseResponse:
        try:
            uid = uuid.UUID(expense_id)
        except ValueError:
            raise ExpenseNotFoundError(expense_id)

        expense = self._repo.get_by_id(uid)
        if expense is None:
            raise ExpenseNotFoundError(expense_id)
        return _expense_to_response(expense)

    # ------------------------------------------------------------------
    # List (with filters + pagination)
    # ------------------------------------------------------------------

    def list_expenses(
        self,
        category: Optional[str],
        date_from: Optional[date],
        date_to: Optional[date],
        page: int,
        page_size: int,
    ) -> ExpenseListResponse:
        # Business rule: date_from must be ≤ date_to
        if date_from and date_to and date_from > date_to:
            raise InvalidDateRangeError(str(date_from), str(date_to))

        offset = (page - 1) * page_size
        items, total = self._repo.list(
            category=category,
            date_from=date_from,
            date_to=date_to,
            offset=offset,
            limit=page_size,
        )

        total_pages = max(1, (total + page_size - 1) // page_size)

        return ExpenseListResponse(
            items=[_expense_to_response(e) for e in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_expense(self, expense_id: str) -> None:
        try:
            uid = uuid.UUID(expense_id)
        except ValueError:
            raise ExpenseNotFoundError(expense_id)

        deleted = self._repo.delete(uid)
        if not deleted:
            raise ExpenseNotFoundError(expense_id)

    # ------------------------------------------------------------------
    # Summary — the key differentiator (aggregation logic in the service)
    # ------------------------------------------------------------------

    def get_summary(self, month: int, year: int) -> ExpenseSummary:
        """
        Fetch all expenses for the given month and compute:
        - total spending
        - expense count
        - per-category breakdown (total + count)

        This logic belongs in the service layer — not in the router, not in the repository.
        """
        expenses = self._repo.get_by_month(month=month, year=year)

        total_spending = 0.0
        category_totals: dict[str, float] = defaultdict(float)
        category_counts: dict[str, int] = defaultdict(int)

        for expense in expenses:
            total_spending += expense.amount
            category_totals[expense.category] += expense.amount
            category_counts[expense.category] += 1

        breakdown = [
            CategoryBreakdown(
                category=cat,
                total=round(category_totals[cat], 2),
                count=category_counts[cat],
            )
            for cat in sorted(category_totals.keys())
        ]

        return ExpenseSummary(
            month=month,
            year=year,
            total_spending=round(total_spending, 2),
            expense_count=len(expenses),
            breakdown=breakdown,
        )
