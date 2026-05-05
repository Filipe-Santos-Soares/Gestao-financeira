import unittest

from finance_logic import calculate_summary


class FinanceLogicTest(unittest.TestCase):
    def test_salary_without_expenses(self):
        summary = calculate_summary("3500,00", [], [])

        self.assertEqual(summary["salary"], 3500.00)
        self.assertEqual(summary["total_expenses"], 0.00)
        self.assertEqual(summary["remaining_balance"], 3500.00)
        self.assertEqual(summary["committed_percentage"], 0.00)
        self.assertEqual(summary["available_percentage"], 100.00)
        self.assertFalse(summary["is_over_budget"])

    def test_fixed_and_variable_expenses(self):
        summary = calculate_summary(
            "3500,00",
            [{"description": "Aluguel", "amount": "1200,00"}],
            [{"description": "Mercado", "amount": "450,50"}],
        )

        self.assertEqual(summary["fixed_total"], 1200.00)
        self.assertEqual(summary["variable_total"], 450.50)
        self.assertEqual(summary["total_expenses"], 1650.50)
        self.assertEqual(summary["remaining_balance"], 1849.50)

    def test_over_budget(self):
        summary = calculate_summary(
            1000,
            [{"description": "Aluguel", "amount": 900}],
            [{"description": "Compra", "amount": 250}],
        )

        self.assertEqual(summary["remaining_balance"], -150.00)
        self.assertTrue(summary["is_over_budget"])
        self.assertEqual(summary["chart"]["values"], [900.00, 250.00, 0.00])

    def test_zero_salary_avoids_invalid_percentage(self):
        summary = calculate_summary(
            0,
            [{"description": "Conta", "amount": 100}],
            [],
        )

        self.assertEqual(summary["committed_percentage"], 0.00)
        self.assertEqual(summary["available_percentage"], 0.00)
        self.assertFalse(summary["has_salary"])

    def test_negative_values_are_ignored(self):
        summary = calculate_summary(
            "-1000",
            [{"description": "Conta", "amount": "-100"}],
            [{"description": "Mercado", "amount": "50"}],
        )

        self.assertEqual(summary["salary"], 0.00)
        self.assertEqual(summary["fixed_total"], 0.00)
        self.assertEqual(summary["variable_total"], 50.00)

    def test_optional_category_is_preserved(self):
        summary = calculate_summary(
            "2000,00",
            [{"description": "Internet", "category": "Casa", "amount": "120,00"}],
            [{"description": "Cinema", "category": "", "amount": "80,00"}],
        )

        self.assertEqual(summary["fixed_expenses"][0]["category"], "Casa")
        self.assertEqual(summary["variable_expenses"][0]["category"], "")
        self.assertEqual(summary["total_expenses"], 200.00)

    def test_dot_decimal_is_supported_by_api_logic(self):
        summary = calculate_summary(
            "1000.50",
            [{"description": "Conta", "amount": "100.25"}],
            [],
        )

        self.assertEqual(summary["salary"], 1000.50)
        self.assertEqual(summary["fixed_total"], 100.25)


if __name__ == "__main__":
    unittest.main()
