import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas (API → Service)
# ---------------------------------------------------------------------------

class ExpenseCreate(BaseModel):
    """Request body for POST /expenses."""

    title: str = Field(..., min_length=1, max_length=255, description="Short label for the expense")
    amount: float = Field(..., gt=0, description="Amount spent (must be positive)")
    category: str = Field(..., min_length=1, max_length=100, description="Expense category (e.g. Food, Travel)")
    date: datetime.date = Field(..., description="Date of the expense (YYYY-MM-DD)")
    description: Optional[str] = Field(None, max_length=1000, description="Optional notes")


# ---------------------------------------------------------------------------
# Response schemas (Service → API)
# ---------------------------------------------------------------------------

class ExpenseResponse(BaseModel):
    """Response shape for a single expense — returned by create, get-by-id."""

    id: uuid.UUID
    title: str
    amount: float
    category: str
    date: datetime.date
    description: Optional[str]
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class ExpenseListResponse(BaseModel):
    """Paginated list of expenses."""

    items: list[ExpenseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# Summary schemas
# ---------------------------------------------------------------------------

class CategoryBreakdown(BaseModel):
    """Spending total for a single category within the requested month."""

    category: str
    total: float
    count: int


class ExpenseSummary(BaseModel):
    """Response for GET /expenses/summary."""

    month: int
    year: int
    total_spending: float
    expense_count: int
    breakdown: list[CategoryBreakdown]
