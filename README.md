# Expense Tracker API - Screenshots

### 1. Interactive Swagger UI API Documentation
This screenshot shows the automatically generated interactive API documentation playground provided by FastAPI. It lists all five implemented endpoints: `POST`, `GET`, `GET by ID`, `DELETE`, and `GET summary`.
![Swagger UI](docs/swagger_ui.png)

### 2. Creating an Expense (POST /expenses)
This shows the expanded `POST /expenses` endpoint, demonstrating how a user can create a new expense by inputting the title, amount, category, date, and optional description. It responds with the saved expense details along with its unique ID.
![POST Expense Detail](docs/post_expense_expanded.png)

### 3. Monthly Spend Summary (GET /expenses/summary)
This shows the `GET /expenses/summary` endpoint execution, which takes a target month and year and calculates the total spending for that month, accompanied by a clean category-wise cost breakdown.
![GET Summary Detail](docs/get_summary_expanded.png)
