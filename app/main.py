from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.features.expenses.exceptions import ExpenseNotFoundError, InvalidDateRangeError
from app.features.expenses.router import router as expense_router

app = FastAPI(
    title="Expense Tracker API",
    description=(
        "A production-grade expense tracking REST API built with FastAPI, "
        "Supabase, and clean layered architecture."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Global exception handlers — translate domain exceptions to HTTP responses.
# This is the only place in the codebase that maps domain errors to HTTP codes.
# ---------------------------------------------------------------------------

@app.exception_handler(ExpenseNotFoundError)
async def expense_not_found_handler(
    request: Request, exc: ExpenseNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


@app.exception_handler(InvalidDateRangeError)
async def invalid_date_range_handler(
    request: Request, exc: InvalidDateRangeError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )


# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------

app.include_router(expense_router)


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {"message": "Expense Tracker API", "docs": "/docs"}
