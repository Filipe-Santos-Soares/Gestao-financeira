import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from repositories import SQLiteBudgetRepository


class SQLiteBudgetRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        self.repository = SQLiteBudgetRepository(self.database_path)
        self.repository.init_schema()

    def tearDown(self):
        self.repository.close()
        self.temp_dir.cleanup()

    def test_create_user_without_email(self):
        user = self.repository.create_user("Usuario teste", "hash-simulado")

        self.assertIsNotNone(user.id)
        self.assertEqual(user.name, "Usuario teste")
        self.assertEqual(user.password_hash, "hash-simulado")
        self.assertFalse(hasattr(user, "email"))

    def test_get_or_create_user_reuses_existing_user(self):
        first_user = self.repository.get_or_create_user("Usuario local", "hash-simulado")
        second_user = self.repository.get_or_create_user("Usuario local", "outro-hash")

        self.assertEqual(first_user.id, second_user.id)
        self.assertEqual(second_user.password_hash, "hash-simulado")

    def test_create_month_budget(self):
        user = self.repository.create_user("Usuario teste", "hash-simulado")
        budget = self.repository.create_month_budget(user.id, 5, 2026, Decimal("3500.00"))

        self.assertIsNotNone(budget.id)
        self.assertEqual(budget.user_id, user.id)
        self.assertEqual(budget.month, 5)
        self.assertEqual(budget.year, 2026)
        self.assertEqual(budget.salary, Decimal("3500.00"))

    def test_add_and_list_expenses_with_optional_category(self):
        user = self.repository.create_user("Usuario teste", "hash-simulado")
        budget = self.repository.create_month_budget(user.id, 5, 2026, Decimal("3500.00"))

        fixed_expense = self.repository.add_expense(
            month_budget_id=budget.id,
            expense_type="fixed",
            description="Aluguel",
            category="Moradia",
            amount=Decimal("1200.00"),
        )
        variable_expense = self.repository.add_expense(
            month_budget_id=budget.id,
            expense_type="variable",
            description="Mercado",
            amount=Decimal("450.00"),
        )

        all_expenses = self.repository.list_expenses(budget.id)
        fixed_expenses = self.repository.list_expenses(budget.id, "fixed")

        self.assertEqual(len(all_expenses), 2)
        self.assertEqual(len(fixed_expenses), 1)
        self.assertEqual(fixed_expense.category, "Moradia")
        self.assertEqual(variable_expense.category, "")
        self.assertEqual(variable_expense.amount, Decimal("450.00"))

    def test_update_month_budget_salary(self):
        user = self.repository.create_user("Usuario teste", "hash-simulado")
        budget = self.repository.create_month_budget(user.id, 5, 2026, Decimal("3500.00"))

        updated_budget = self.repository.update_month_budget_salary(budget.id, Decimal("4200.50"))

        self.assertEqual(updated_budget.salary, Decimal("4200.50"))

    def test_list_month_budgets_returns_most_recent_first(self):
        user = self.repository.create_user("Usuario teste", "hash-simulado")
        self.repository.create_month_budget(user.id, 5, 2026, Decimal("3500.00"))
        self.repository.create_month_budget(user.id, 6, 2026, Decimal("4200.00"))
        self.repository.create_month_budget(user.id, 12, 2025, Decimal("3000.00"))

        budgets = self.repository.list_month_budgets(user.id)

        self.assertEqual([(budget.month, budget.year) for budget in budgets], [(6, 2026), (5, 2026), (12, 2025)])

    def test_delete_expense(self):
        user = self.repository.create_user("Usuario teste", "hash-simulado")
        budget = self.repository.create_month_budget(user.id, 5, 2026, Decimal("3500.00"))
        expense = self.repository.add_expense(
            month_budget_id=budget.id,
            expense_type="fixed",
            description="Internet",
            category="Casa",
            amount=Decimal("120.00"),
        )

        deleted = self.repository.delete_expense(expense.id)

        self.assertTrue(deleted)
        self.assertEqual(self.repository.list_expenses(budget.id), [])

    def test_create_and_list_categories(self):
        user = self.repository.create_user("Usuario teste", "hash-simulado")

        category = self.repository.create_category(user.id, "Moradia", "fixed")

        categories = self.repository.list_categories(user.id)

        self.assertIsNotNone(category.id)
        self.assertEqual(category.name, "Moradia")
        self.assertEqual(category.type, "fixed")
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0].name, "Moradia")


if __name__ == "__main__":
    unittest.main()
