import unittest
from datetime import datetime

from validation import (
    is_valid_money_value,
    parse_period,
    parse_year,
    validate_category_payload,
    validate_month_budget_payload,
)


class ValidationTest(unittest.TestCase):
    def test_parse_period_uses_payload_values(self):
        month, year, error = parse_period({"month": "5", "year": "2026"})

        self.assertEqual(month, 5)
        self.assertEqual(year, 2026)
        self.assertIsNone(error)

    def test_parse_period_uses_current_date_as_fallback(self):
        month, year, error = parse_period(now=datetime(2026, 5, 14))

        self.assertEqual(month, 5)
        self.assertEqual(year, 2026)
        self.assertIsNone(error)

    def test_parse_period_rejects_invalid_values(self):
        self.assertIn("mês entre 1 e 12", parse_period({"month": "13", "year": "2026"})[2])
        self.assertIn("ano entre 1900 e 9999", parse_period({"month": "5", "year": "1899"})[2])
        self.assertIn("números válidos", parse_period({"month": "maio", "year": "2026"})[2])

    def test_parse_year_rejects_invalid_values(self):
        year, error = parse_year({"year": "2026"})

        self.assertEqual(year, 2026)
        self.assertIsNone(error)
        self.assertIn("Ano deve ser", parse_year({"year": "abc"})[1])
        self.assertIn("ano entre 1900 e 9999", parse_year({"year": "10000"})[1])

    def test_money_validation_accepts_supported_formats(self):
        valid_values = ["", None, "1000", "1000,00", "1.000,00", "1000.00", "R$ 1.000,00", 1000]

        for value in valid_values:
            with self.subTest(value=value):
                self.assertTrue(is_valid_money_value(value))

    def test_money_validation_rejects_invalid_formats(self):
        invalid_values = ["valor", "-10", "10,999", "1.00.0", object()]

        for value in invalid_values:
            with self.subTest(value=value):
                self.assertFalse(is_valid_money_value(value))

    def test_validate_category_payload_normalizes_valid_data(self):
        payload, error = validate_category_payload(
            {"name": "  Moradia  ", "type": "fixed", "goal_amount": "1.200,00"}
        )

        self.assertIsNone(error)
        self.assertEqual(payload["name"], "Moradia")
        self.assertEqual(payload["type"], "fixed")
        self.assertEqual(payload["goal_amount"], "1.200,00")

    def test_validate_category_payload_rejects_invalid_data(self):
        self.assertIn("Informe o nome", validate_category_payload({"name": ""})[1])
        self.assertIn("Tipo de categoria", validate_category_payload({"name": "Casa", "type": "outro"})[1])
        self.assertIn("no máximo 40", validate_category_payload({"name": "C" * 41})[1])
        self.assertIn("Meta mensal", validate_category_payload({"name": "Casa", "goal_amount": "abc"})[1])

    def test_validate_month_budget_payload_normalizes_expenses(self):
        payload, error = validate_month_budget_payload(
            {
                "month": 5,
                "year": 2026,
                "salary": "3500,00",
                "fixed_expenses": [
                    {"description": "", "category": "", "amount": ""},
                    {"description": " Aluguel ", "category": " Moradia ", "amount": "1200,00"},
                ],
                "variable_expenses": None,
            }
        )

        self.assertIsNone(error)
        self.assertEqual(payload["month"], 5)
        self.assertEqual(payload["year"], 2026)
        self.assertEqual(len(payload["fixed_expenses"]), 1)
        self.assertEqual(payload["fixed_expenses"][0]["description"], "Aluguel")
        self.assertEqual(payload["fixed_expenses"][0]["category"], "Moradia")
        self.assertEqual(payload["variable_expenses"], [])

    def test_validate_month_budget_payload_rejects_invalid_data(self):
        self.assertIn("Salário deve ser", validate_month_budget_payload({"salary": "abc"})[1])
        self.assertIn(
            "devem ser enviados em uma lista",
            validate_month_budget_payload({"fixed_expenses": "Aluguel"})[1],
        )
        self.assertIn(
            "Informe o valor",
            validate_month_budget_payload({"fixed_expenses": [{"description": "Aluguel", "amount": ""}]})[1],
        )


if __name__ == "__main__":
    unittest.main()
