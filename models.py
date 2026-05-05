from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class User:
    id: int | None
    name: str
    password_hash: str
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(frozen=True)
class MonthBudget:
    id: int | None
    user_id: int
    month: int
    year: int
    salary: Decimal
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(frozen=True)
class Expense:
    id: int | None
    month_budget_id: int
    type: str
    description: str
    category: str
    amount: Decimal
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(frozen=True)
class Category:
    id: int | None
    user_id: int
    name: str
    type: str
    created_at: str | None = None
    updated_at: str | None = None
