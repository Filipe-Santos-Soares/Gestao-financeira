from datetime import datetime
from decimal import Decimal, InvalidOperation
import re


CATEGORY_TYPES = {"fixed", "variable", "both"}
MAX_CATEGORY_NAME_LENGTH = 40
MAX_EXPENSE_DESCRIPTION_LENGTH = 80
MAX_EXPENSE_CATEGORY_LENGTH = 40
MONEY_PATTERN = re.compile(
    r"^(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d{1,2})?$|^\d+(?:\.\d{1,2})?$"
)


def _source_value(key, payload, query_args, default):
    payload = payload or {}
    query_args = query_args or {}
    return payload.get(key) or query_args.get(key) or default


def parse_period(payload=None, query_args=None, now=None):
    now = now or datetime.now()
    raw_month = _source_value("month", payload, query_args, now.month)
    raw_year = _source_value("year", payload, query_args, now.year)

    try:
        month = int(raw_month)
        year = int(raw_year)
    except (TypeError, ValueError):
        return None, None, "Mês e ano devem ser números válidos."

    if month < 1 or month > 12:
        return None, None, "Informe um mês entre 1 e 12."

    if year < 1900 or year > 9999:
        return None, None, "Informe um ano entre 1900 e 9999."

    return month, year, None


def parse_year(payload=None, query_args=None, now=None):
    now = now or datetime.now()
    raw_year = _source_value("year", payload, query_args, now.year)

    try:
        year = int(raw_year)
    except (TypeError, ValueError):
        return None, "Ano deve ser um número válido."

    if year < 1900 or year > 9999:
        return None, "Informe um ano entre 1900 e 9999."

    return year, None


def normalize_money_text(value):
    return str(value or "").strip().replace("R$", "").replace(" ", "")


def is_blank_money_value(value):
    if value is None:
        return True

    if isinstance(value, (int, float, Decimal)):
        return False

    return normalize_money_text(value) == ""


def is_valid_money_value(value):
    if value is None or value == "":
        return True

    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value)) >= 0
        except (InvalidOperation, ValueError):
            return False

    normalized = normalize_money_text(value)

    if not normalized:
        return True

    if normalized.startswith("-"):
        return False

    return bool(MONEY_PATTERN.fullmatch(normalized))


def is_zero_or_blank_money(value):
    if value is None or value == "":
        return True

    if not is_valid_money_value(value):
        return False

    normalized = normalize_money_text(value)

    if not normalized:
        return True

    if "," in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif normalized.count(".") > 1:
        normalized = normalized.replace(".", "")

    try:
        return Decimal(normalized) == 0
    except (InvalidOperation, ValueError):
        return False


def validate_category_payload(payload):
    payload = payload or {}
    name = str(payload.get("name", "")).strip()
    category_type = str(payload.get("type", "both")).strip() or "both"
    goal_amount = payload.get("goal_amount", "")

    if category_type not in CATEGORY_TYPES:
        return None, "Tipo de categoria inválido."

    if not name:
        return None, "Informe o nome da categoria."

    if len(name) > MAX_CATEGORY_NAME_LENGTH:
        return None, f"O nome da categoria deve ter no máximo {MAX_CATEGORY_NAME_LENGTH} caracteres."

    if not is_valid_money_value(goal_amount):
        return None, "Meta mensal deve ser um valor monetário válido."

    return {
        "name": name,
        "type": category_type,
        "goal_amount": goal_amount,
    }, None


def validate_expenses_payload(expenses, expense_label):
    if expenses is None:
        return [], None

    if not isinstance(expenses, list):
        return None, f"Gastos {expense_label} devem ser enviados em uma lista."

    normalized_expenses = []

    for index, expense in enumerate(expenses, start=1):
        if not isinstance(expense, dict):
            return None, f"Gasto {expense_label} #{index} deve ser um objeto válido."

        description = str(expense.get("description", "")).strip()
        category = str(expense.get("category", "")).strip()
        amount = expense.get("amount", "")
        has_text = bool(description or category)
        has_amount = not is_zero_or_blank_money(amount)

        if len(description) > MAX_EXPENSE_DESCRIPTION_LENGTH:
            return None, f"Descrição do gasto {expense_label} #{index} deve ter no máximo {MAX_EXPENSE_DESCRIPTION_LENGTH} caracteres."

        if len(category) > MAX_EXPENSE_CATEGORY_LENGTH:
            return None, f"Categoria do gasto {expense_label} #{index} deve ter no máximo {MAX_EXPENSE_CATEGORY_LENGTH} caracteres."

        if not is_valid_money_value(amount):
            return None, f"Valor do gasto {expense_label} #{index} deve ser um valor monetário válido."

        if has_text and is_blank_money_value(amount):
            return None, f"Informe o valor do gasto {expense_label} #{index}."

        if not has_text and not has_amount:
            continue

        normalized_expenses.append(
            {
                "description": description,
                "category": category,
                "amount": amount,
            }
        )

    return normalized_expenses, None


def validate_month_budget_payload(payload, query_args=None):
    payload = payload or {}
    month, year, period_error = parse_period(payload, query_args)

    if period_error:
        return None, period_error

    salary = payload.get("salary", 0)

    if not is_valid_money_value(salary):
        return None, "Salário deve ser um valor monetário válido."

    fixed_expenses, fixed_error = validate_expenses_payload(payload.get("fixed_expenses", []), "fixo")

    if fixed_error:
        return None, fixed_error

    variable_expenses, variable_error = validate_expenses_payload(payload.get("variable_expenses", []), "variado")

    if variable_error:
        return None, variable_error

    return {
        "month": month,
        "year": year,
        "salary": salary,
        "fixed_expenses": fixed_expenses,
        "variable_expenses": variable_expenses,
    }, None
