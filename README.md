# Expense Tracker API

A production-grade REST API for tracking expenses, built with **FastAPI**, **Supabase (PostgreSQL)**, and clean layered architecture.

---

## Architecture

```
app/
├── main.py                  # FastAPI app, exception handlers, router registration
├── config.py                # pydantic-settings — loads SUPABASE_URL & SUPABASE_KEY from .env
├── dependencies.py          # FastAPI Depends wiring: client → repository → service
├── database/
│   └── supabase_client.py   # Supabase client factory — created once, injected via DI
└── features/
    └── expenses/
        ├── router.py        # HTTP layer only — parses params, calls service, returns response
        ├── service.py       # Business logic — aggregation, validation, domain exceptions
        ├── repository.py    # Abstract interface + SupabaseExpenseRepository implementation
        ├── schemas.py       # Pydantic v2 request/response schemas
        ├── models.py        # Internal domain model (Expense dataclass)
        └── exceptions.py    # Domain exceptions (ExpenseNotFoundError, etc.)
tests/
├── conftest.py
├── test_expense_service.py  # Unit tests — FakeExpenseRepository (in-memory), no real DB
└── test_expense_router.py   # Router tests — TestClient + dependency overrides
```

### Layer Responsibilities

| Layer | Responsibility |
|-------|---------------|
| **Router** | HTTP only — parse request, call service, return response. Zero business logic. |
| **Service** | All business rules — summary aggregation, pagination logic, domain exceptions. Talks only to Repository. |
| **Repository** | Data access abstraction — abstract interface + Supabase concrete implementation. |
| **Schemas** | Pydantic v2 — API-facing request/response models, separate from domain models. |
| **Domain Models** | Internal representations used across service and repository layers. |

### Key Architectural Decisions

- **Dependency Injection via FastAPI `Depends`**: Every layer receives its dependencies from the outside. The Supabase client is created once and injected into the repository; the repository is injected into the service; the service is injected into the router.
- **Abstract Repository Interface**: `AbstractExpenseRepository` (ABC) makes the service testable with `FakeExpenseRepository` — no real DB required in unit tests.
- **Domain exceptions, not HTTP exceptions**: The service raises `ExpenseNotFoundError`; the router (or exception handler in `main.py`) converts it to a `404` response.
- **pydantic-settings for config**: All secrets come from `.env` — no hardcoded values anywhere.

---

## Setup

### 1. Clone and install dependencies

```bash
cd "expense tracker"
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up Supabase

> **You need to do this once:**

1. Go to [supabase.com](https://supabase.com) and create a free project.
2. In the Supabase dashboard, open **SQL Editor** and run:

```sql
CREATE TABLE expenses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  amount NUMERIC(10, 2) NOT NULL,
  category TEXT NOT NULL,
  date DATE NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

3. Go to **Project Settings → API** and copy:
   - **Project URL**
   - **anon / public key**

### 3. Configure environment

```bash
cp .env.example .env
# Open .env and fill in your SUPABASE_URL and SUPABASE_KEY
```

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

API docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/expenses` | Create a new expense |
| `GET` | `/expenses` | List expenses (filter by category, date range; paginated) |
| `GET` | `/expenses/{id}` | Get a single expense by ID |
| `DELETE` | `/expenses/{id}` | Delete an expense |
| `GET` | `/expenses/summary` | Monthly summary — total spend + breakdown by category |

### Query Parameters

**`GET /expenses`**
- `category` — filter by category (optional)
- `date_from` — start date `YYYY-MM-DD` (optional)
- `date_to` — end date `YYYY-MM-DD` (optional)
- `page` — page number, default `1`
- `page_size` — items per page, default `20`, max `100`

**`GET /expenses/summary`**
- `month` — integer 1–12 (required)
- `year` — integer e.g. 2024 (required)

### Example Request

```bash
# Create an expense
curl -X POST http://localhost:8000/expenses \
  -H "Content-Type: application/json" \
  -d '{"title": "Lunch", "amount": 12.50, "category": "Food", "date": "2024-06-15"}'

# Get monthly summary
curl "http://localhost:8000/expenses/summary?month=6&year=2024"
```

---

## Screenshots

### 1. Interactive Swagger UI API Documentation
This screenshot shows the automatically generated interactive API documentation playground provided by FastAPI. It lists all five implemented endpoints: `POST`, `GET`, `GET by ID`, `DELETE`, and `GET summary`.
![Swagger UI](docs/swagger_ui.png)

### 2. Creating an Expense (POST /expenses)
This shows the expanded `POST /expenses` endpoint, demonstrating how a user can create a new expense by inputting the title, amount, category, date, and optional description. It responds with the saved expense details along with its unique ID.
![POST Expense Detail](docs/post_expense_expanded.png)

### 3. Monthly Spend Summary (GET /expenses/summary)
This shows the `GET /expenses/summary` endpoint execution, which takes a target month and year and calculates the total spending for that month, accompanied by a clean category-wise cost breakdown.
![GET Summary Detail](docs/get_summary_expanded.png)

---

## Running Tests

```bash
pytest tests/ -v
```

Tests do **not** require a real Supabase connection. Service tests use `FakeExpenseRepository` (in-memory list). Router tests use FastAPI's `TestClient` with dependency overrides.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Your Supabase anon/public key |

See `.env.example` for the template.
