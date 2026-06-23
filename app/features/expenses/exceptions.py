class ExpenseNotFoundError(Exception):
    """Raised by the service when an expense with the given ID does not exist."""

    def __init__(self, expense_id: str) -> None:
        self.expense_id = expense_id
        super().__init__(f"Expense with id '{expense_id}' was not found.")


class InvalidDateRangeError(Exception):
    """Raised when date_from is after date_to in a list/filter request."""

    def __init__(self, date_from: str, date_to: str) -> None:
        self.date_from = date_from
        self.date_to = date_to
        super().__init__(
            f"Invalid date range: date_from ({date_from}) must be before date_to ({date_to})."
        )
