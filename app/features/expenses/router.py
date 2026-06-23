from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_expense_service
from app.features.expenses.exceptions import ExpenseNotFoundError, InvalidDateRangeError
from app.features.expenses.schemas import (
    ExpenseCreate,
    ExpenseListResponse,
    ExpenseResponse,
    ExpenseSummary,
)
from app.features.expenses.service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["Expenses"])


# ---------------------------------------------------------------------------
# POST /expenses — Create a new expense
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an expense",
)
def create_expense(
    body: ExpenseCreate,
    service: ExpenseService = Depends(get_expense_service),
) -> ExpenseResponse:
    return service.create_expense(body)


# ---------------------------------------------------------------------------
# GET /expenses/summary — Monthly summary
# NOTE: This route MUST be defined BEFORE /expenses/{id} so FastAPI does not
#       try to match "summary" as an {id} path parameter.
# ---------------------------------------------------------------------------

@router.get(
    "/summary",
    response_model=ExpenseSummary,
    summary="Get monthly spending summary",
)
def get_summary(
    month: int = Query(..., ge=1, le=12, description="Month (1–12)"),
    year: int = Query(..., ge=2000, le=2100, description="Year (e.g. 2024)"),
    service: ExpenseService = Depends(get_expense_service),
) -> ExpenseSummary:
    return service.get_summary(month=month, year=year)


# ---------------------------------------------------------------------------
# GET /expenses — List expenses with optional filters and pagination
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=ExpenseListResponse,
    summary="List expenses",
)
def list_expenses(
    category: Optional[str] = Query(None, description="Filter by category"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: ExpenseService = Depends(get_expense_service),
) -> ExpenseListResponse:
    try:
        return service.list_expenses(
            category=category,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
        )
    except InvalidDateRangeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# GET /expenses/{id} — Get a single expense
# ---------------------------------------------------------------------------

@router.get(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Get expense by ID",
)
def get_expense(
    expense_id: str,
    service: ExpenseService = Depends(get_expense_service),
) -> ExpenseResponse:
    try:
        return service.get_expense(expense_id)
    except ExpenseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# DELETE /expenses/{id} — Delete an expense
# ---------------------------------------------------------------------------

@router.delete(
    "/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an expense",
)
def delete_expense(
    expense_id: str,
    service: ExpenseService = Depends(get_expense_service),
) -> None:
    try:
        service.delete_expense(expense_id)
    except ExpenseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
