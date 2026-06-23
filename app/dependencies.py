from fastapi import Depends
from supabase import Client

from app.database.supabase_client import get_supabase_client
from app.features.expenses.repository import AbstractExpenseRepository, SupabaseExpenseRepository
from app.features.expenses.service import ExpenseService


def get_repository(
    client: Client = Depends(get_supabase_client),
) -> AbstractExpenseRepository:
    """
    Constructs the Supabase repository with an injected Supabase client.
    Returns the abstract type so the service never depends on the concrete class.
    """
    return SupabaseExpenseRepository(client=client)


def get_expense_service(
    repository: AbstractExpenseRepository = Depends(get_repository),
) -> ExpenseService:
    """
    Constructs the ExpenseService with an injected repository.
    Used in all router endpoints via Depends(get_expense_service).
    """
    return ExpenseService(repository=repository)
