import sqlite3
from decimal import Decimal
from pathlib import Path

from finance_logic import to_decimal
from models import Category, Expense, MonthBudget, User


SCHEMA_PATH = Path(__file__).resolve().parent.parent / "database" / "schema.sql"
MONEY_QUANT = Decimal("0.01")
POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS month_budgets (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
  year INTEGER NOT NULL CHECK (year >= 1900),
  salary TEXT NOT NULL DEFAULT '0.00',
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, month, year)
);

CREATE TABLE IF NOT EXISTS expenses (
  id SERIAL PRIMARY KEY,
  month_budget_id INTEGER NOT NULL REFERENCES month_budgets (id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK (type IN ('fixed', 'variable')),
  description TEXT NOT NULL DEFAULT '',
  category TEXT NOT NULL DEFAULT '',
  amount TEXT NOT NULL DEFAULT '0.00',
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  type TEXT NOT NULL DEFAULT 'both' CHECK (type IN ('fixed', 'variable', 'both')),
  goal_amount TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, name, type)
);

CREATE INDEX IF NOT EXISTS idx_month_budgets_user_period
ON month_budgets (user_id, year, month);

CREATE INDEX IF NOT EXISTS idx_expenses_month_budget
ON expenses (month_budget_id);

CREATE INDEX IF NOT EXISTS idx_categories_user
ON categories (user_id);
"""


def money_to_storage(value):
    return str(to_decimal(value).quantize(MONEY_QUANT))


def storage_to_money(value):
    return Decimal(str(value)).quantize(MONEY_QUANT)


def optional_money_to_storage(value):
    if value is None or value == "":
        return ""

    amount = to_decimal(value).quantize(MONEY_QUANT)

    if amount <= 0:
        return ""

    return str(amount)


def optional_storage_to_money(value):
    if value is None or value == "":
        return None

    return Decimal(str(value)).quantize(MONEY_QUANT)


class SQLiteBudgetRepository:
    paramstyle = "qmark"

    def __init__(self, database_path):
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def execute(self, query, params=()):
        return self.connection.execute(query, params)

    def fetchone(self, query, params=()):
        return self.execute(query, params).fetchone()

    def fetchall(self, query, params=()):
        return self.execute(query, params).fetchall()

    def insert_and_get_id(self, query, params):
        cursor = self.execute(query, params)
        return cursor.lastrowid

    def close(self):
        self.connection.close()

    def init_schema(self):
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        self.connection.executescript(schema)
        self.ensure_category_goal_column()
        self.connection.commit()

    def ensure_category_goal_column(self):
        columns = {row["name"] for row in self.fetchall("PRAGMA table_info(categories)")}

        if "goal_amount" not in columns:
            self.execute("ALTER TABLE categories ADD COLUMN goal_amount TEXT NOT NULL DEFAULT ''")

    def create_user(self, name, password_hash):
        user_id = self.insert_and_get_id(
            """
            INSERT INTO users (name, password_hash)
            VALUES (?, ?)
            """,
            (name, password_hash),
        )
        self.connection.commit()

        return self.get_user(user_id)

    def get_or_create_user(self, name, password_hash):
        user = self.get_user_by_name(name)

        if user:
            return user

        return self.create_user(name, password_hash)

    def update_user_password_hash(self, user_id, password_hash):
        self.execute(
            """
            UPDATE users
            SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (password_hash, user_id),
        )
        self.connection.commit()

        return self.get_user(user_id)

    def get_user(self, user_id):
        row = self.fetchone(
            """
            SELECT id, name, password_hash, created_at, updated_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        )

        if row is None:
            return None

        return User(
            id=row["id"],
            name=row["name"],
            password_hash=row["password_hash"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_user_by_name(self, name):
        row = self.fetchone(
            """
            SELECT id, name, password_hash, created_at, updated_at
            FROM users
            WHERE name = ?
            ORDER BY id
            LIMIT 1
            """,
            (name,),
        )

        if row is None:
            return None

        return User(
            id=row["id"],
            name=row["name"],
            password_hash=row["password_hash"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def create_month_budget(self, user_id, month, year, salary):
        month_budget_id = self.insert_and_get_id(
            """
            INSERT INTO month_budgets (user_id, month, year, salary)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, month, year, money_to_storage(salary)),
        )
        self.connection.commit()

        return self.get_month_budget_by_id(month_budget_id)

    def get_or_create_month_budget(self, user_id, month, year, salary="0.00"):
        budget = self.get_month_budget(user_id, month, year)

        if budget:
            return budget

        return self.create_month_budget(user_id, month, year, salary)

    def get_month_budget(self, user_id, month, year):
        row = self.fetchone(
            """
            SELECT id, user_id, month, year, salary, created_at, updated_at
            FROM month_budgets
            WHERE user_id = ? AND month = ? AND year = ?
            """,
            (user_id, month, year),
        )

        return self._month_budget_from_row(row)

    def get_month_budget_by_id(self, month_budget_id):
        row = self.fetchone(
            """
            SELECT id, user_id, month, year, salary, created_at, updated_at
            FROM month_budgets
            WHERE id = ?
            """,
            (month_budget_id,),
        )

        return self._month_budget_from_row(row)

    def list_month_budgets(self, user_id):
        rows = self.fetchall(
            """
            SELECT id, user_id, month, year, salary, created_at, updated_at
            FROM month_budgets
            WHERE user_id = ?
            ORDER BY year DESC, month DESC
            """,
            (user_id,),
        )

        return [self._month_budget_from_row(row) for row in rows]

    def update_month_budget_salary(self, month_budget_id, salary):
        self.execute(
            """
            UPDATE month_budgets
            SET salary = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (money_to_storage(salary), month_budget_id),
        )
        self.connection.commit()

        return self.get_month_budget_by_id(month_budget_id)

    def add_expense(self, month_budget_id, expense_type, description, amount, category=""):
        expense_id = self.insert_and_get_id(
            """
            INSERT INTO expenses (month_budget_id, type, description, category, amount)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                month_budget_id,
                expense_type,
                description or "",
                category or "",
                money_to_storage(amount),
            ),
        )
        self.connection.commit()

        return self.get_expense(expense_id)

    def clear_expenses(self, month_budget_id):
        self.execute(
            """
            DELETE FROM expenses
            WHERE month_budget_id = ?
            """,
            (month_budget_id,),
        )
        self.connection.commit()

    def replace_expenses(self, month_budget_id, fixed_expenses=None, variable_expenses=None):
        self.clear_expenses(month_budget_id)

        saved_expenses = []

        for expense in fixed_expenses or []:
            saved_expenses.append(
                self.add_expense(
                    month_budget_id=month_budget_id,
                    expense_type="fixed",
                    description=expense.get("description", ""),
                    category=expense.get("category", ""),
                    amount=expense.get("amount", 0),
                )
            )

        for expense in variable_expenses or []:
            saved_expenses.append(
                self.add_expense(
                    month_budget_id=month_budget_id,
                    expense_type="variable",
                    description=expense.get("description", ""),
                    category=expense.get("category", ""),
                    amount=expense.get("amount", 0),
                )
            )

        return saved_expenses

    def get_expense(self, expense_id):
        row = self.fetchone(
            """
            SELECT id, month_budget_id, type, description, category, amount, created_at, updated_at
            FROM expenses
            WHERE id = ?
            """,
            (expense_id,),
        )

        return self._expense_from_row(row)

    def list_expenses(self, month_budget_id, expense_type=None):
        params = [month_budget_id]
        query = """
            SELECT id, month_budget_id, type, description, category, amount, created_at, updated_at
            FROM expenses
            WHERE month_budget_id = ?
        """

        if expense_type:
            query += " AND type = ?"
            params.append(expense_type)

        query += " ORDER BY id"

        rows = self.fetchall(query, params)
        return [self._expense_from_row(row) for row in rows]

    def delete_expense(self, expense_id):
        cursor = self.execute(
            """
            DELETE FROM expenses
            WHERE id = ?
            """,
            (expense_id,),
        )
        self.connection.commit()

        return cursor.rowcount > 0

    def create_category(self, user_id, name, category_type="both", goal_amount=""):
        category_id = self.insert_and_get_id(
            """
            INSERT INTO categories (user_id, name, type, goal_amount)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, name.strip(), category_type, optional_money_to_storage(goal_amount)),
        )
        self.connection.commit()

        return self.get_category(category_id)

    def update_category(self, category_id, name, category_type="both", goal_amount=""):
        self.execute(
            """
            UPDATE categories
            SET name = ?, type = ?, goal_amount = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (name.strip(), category_type, optional_money_to_storage(goal_amount), category_id),
        )
        self.connection.commit()

        return self.get_category(category_id)

    def delete_category(self, category_id):
        cursor = self.execute(
            """
            DELETE FROM categories
            WHERE id = ?
            """,
            (category_id,),
        )
        self.connection.commit()

        return cursor.rowcount > 0

    def get_category(self, category_id):
        row = self.fetchone(
            """
            SELECT id, user_id, name, type, goal_amount, created_at, updated_at
            FROM categories
            WHERE id = ?
            """,
            (category_id,),
        )

        return self._category_from_row(row)

    def get_category_by_name_and_type(self, user_id, name, category_type):
        row = self.fetchone(
            """
            SELECT id, user_id, name, type, goal_amount, created_at, updated_at
            FROM categories
            WHERE user_id = ? AND lower(name) = lower(?) AND type = ?
            LIMIT 1
            """,
            (user_id, name.strip(), category_type),
        )

        return self._category_from_row(row)

    def list_categories(self, user_id):
        rows = self.fetchall(
            """
            SELECT id, user_id, name, type, goal_amount, created_at, updated_at
            FROM categories
            WHERE user_id = ?
            ORDER BY lower(name), type
            """,
            (user_id,),
        )

        return [self._category_from_row(row) for row in rows]

    def _month_budget_from_row(self, row):
        if row is None:
            return None

        return MonthBudget(
            id=row["id"],
            user_id=row["user_id"],
            month=row["month"],
            year=row["year"],
            salary=storage_to_money(row["salary"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _expense_from_row(self, row):
        if row is None:
            return None

        return Expense(
            id=row["id"],
            month_budget_id=row["month_budget_id"],
            type=row["type"],
            description=row["description"],
            category=row["category"],
            amount=storage_to_money(row["amount"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _category_from_row(self, row):
        if row is None:
            return None

        return Category(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            type=row["type"],
            goal_amount=optional_storage_to_money(row["goal_amount"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class PostgreSQLBudgetRepository(SQLiteBudgetRepository):
    paramstyle = "pyformat"

    def __init__(self, database_url):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError(
                "Instale psycopg[binary] para usar PostgreSQL: pip install -r requirements.txt"
            ) from exc

        self.database_path = database_url
        self.connection = psycopg.connect(database_url, row_factory=dict_row)

    def adapt_query(self, query):
        return query.replace("?", "%s")

    def execute(self, query, params=()):
        return self.connection.execute(self.adapt_query(query), params)

    def insert_and_get_id(self, query, params):
        query = query.strip().rstrip(";")
        row = self.execute(f"{query} RETURNING id", params).fetchone()
        return row["id"]

    def init_schema(self):
        for statement in POSTGRES_SCHEMA.split(";"):
            statement = statement.strip()

            if statement:
                self.connection.execute(statement)
        self.connection.execute("ALTER TABLE categories ADD COLUMN IF NOT EXISTS goal_amount TEXT NOT NULL DEFAULT ''")
        self.connection.commit()

    def close(self):
        self.connection.close()
