from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional
import uuid

from supabase import Client

from app.features.expenses.models import Expense


# ---------------------------------------------------------------------------
# Abstract interface — defines the contract every implementation must fulfil.
# The service layer only knows about this interface, never the concrete class.
# ---------------------------------------------------------------------------

class AbstractExpenseRepository(ABC):

    @abstractmethod
    def create(
        self,
        title: str,
        amount: float,
        category: str,
        expense_date: date,
        description: Optional[str],
    ) -> Expense:
        """Persist a new expense and return the created domain model."""
        ...

    @abstractmethod
    def get_by_id(self, expense_id: uuid.UUID) -> Optional[Expense]:
        """Return the expense with the given ID, or None if not found."""
        ...

    @abstractmethod
    def list(
        self,
        category: Optional[str],
        date_from: Optional[date],
        date_to: Optional[date],
        offset: int,
        limit: int,
    ) -> tuple[list[Expense], int]:
        """
        Return a page of expenses matching the given filters.
        Returns (items, total_count).
        """
        ...

    @abstractmethod
    def delete(self, expense_id: uuid.UUID) -> bool:
        """Delete the expense. Returns True if deleted, False if not found."""
        ...

    @abstractmethod
    def get_by_month(self, month: int, year: int) -> list[Expense]:
        """Return all expenses for the given month and year."""
        ...


# ---------------------------------------------------------------------------
# Concrete Supabase implementation
# ---------------------------------------------------------------------------

def _row_to_expense(row: dict) -> Expense:
    """Translate a Supabase database row (dict) into the Expense domain model."""
    return Expense(
        id=uuid.UUID(row["id"]),
        title=row["title"],
        amount=float(row["amount"]),
        category=row["category"],
        date=date.fromisoformat(row["date"]),
        description=row.get("description"),
        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
    )


class SupabaseExpenseRepository(AbstractExpenseRepository):
    """
    Concrete repository that talks to Supabase (PostgreSQL) via the supabase-py client.
    Receives the Supabase client via constructor injection — never imported globally.
    """

    TABLE = "expenses"

    def __init__(self, client: Client) -> None:
        self._client = client

    def create(
        self,
        title: str,
        amount: float,
        category: str,
        expense_date: date,
        description: Optional[str],
    ) -> Expense:
        payload = {
            "title": title,
            "amount": amount,
            "category": category,
            "date": expense_date.isoformat(),
            "description": description,
        }
        response = self._client.table(self.TABLE).insert(payload).execute()
        return _row_to_expense(response.data[0])

    def get_by_id(self, expense_id: uuid.UUID) -> Optional[Expense]:
        response = (
            self._client.table(self.TABLE)
            .select("*")
            .eq("id", str(expense_id))
            .execute()
        )
        if not response.data:
            return None
        return _row_to_expense(response.data[0])

    def list(
        self,
        category: Optional[str],
        date_from: Optional[date],
        date_to: Optional[date],
        offset: int,
        limit: int,
    ) -> tuple[list[Expense], int]:
        # Count query
        count_query = self._client.table(self.TABLE).select("*", count="exact")
        if category:
            count_query = count_query.eq("category", category)
        if date_from:
            count_query = count_query.gte("date", date_from.isoformat())
        if date_to:
            count_query = count_query.lte("date", date_to.isoformat())
        count_response = count_query.execute()
        total = count_response.count or 0

        # Data query with pagination
        query = self._client.table(self.TABLE).select("*").order("date", desc=True)
        if category:
            query = query.eq("category", category)
        if date_from:
            query = query.gte("date", date_from.isoformat())
        if date_to:
            query = query.lte("date", date_to.isoformat())
        query = query.range(offset, offset + limit - 1)
        response = query.execute()

        items = [_row_to_expense(row) for row in response.data]
        return items, total

    def delete(self, expense_id: uuid.UUID) -> bool:
        response = (
            self._client.table(self.TABLE)
            .delete()
            .eq("id", str(expense_id))
            .execute()
        )
        return len(response.data) > 0

    def get_by_month(self, month: int, year: int) -> list[Expense]:
        # Build first and last day of the month
        from calendar import monthrange

        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])

        response = (
            self._client.table(self.TABLE)
            .select("*")
            .gte("date", first_day.isoformat())
            .lte("date", last_day.isoformat())
            .order("date", desc=False)
            .execute()
        )
        return [_row_to_expense(row) for row in response.data]
