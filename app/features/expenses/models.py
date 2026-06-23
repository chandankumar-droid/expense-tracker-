from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
import uuid


@dataclass
class Expense:
    """
    Internal domain model for an expense.
    Used by the service and repository layers — NOT exposed directly via the API.
    API-facing schemas (ExpenseResponse, etc.) are in schemas.py.
    """

    id: uuid.UUID
    title: str
    amount: float
    category: str
    date: date
    description: Optional[str]
    created_at: datetime
