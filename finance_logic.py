from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


MONEY_QUANT = Decimal("0.01")


def to_decimal(value):
    """Convert UI/API values to a non-negative Decimal."""
    if value is None or value == "":
        return Decimal("0.00")

    if isinstance(value, str):
        normalized = value.strip().replace("R$", "").replace(" ", "")

        if "," in normalized:
            normalized = normalized.replace(".", "").replace(",", ".")
        elif normalized.count(".") == 1 and len(normalized.rsplit(".", 1)[1]) <= 2:
            normalized = normalized
        else:
            normalized = normalized.replace(".", "")
    else:
        normalized = str(value)

    try:
        amount = Decimal(normalized)
    except (InvalidOperation, ValueError):
        amount = Decimal("0.00")

    if amount < 0:
        return Decimal("0.00")

    return amount.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def normalize_expenses(expenses):
    normalized = []

    for expense in expenses or []:
        description = str(expense.get("description", "")).strip()
        category = str(expense.get("category", "")).strip()
        amount = to_decimal(expense.get("amount", 0))

        if not description and not category and amount == 0:
            continue

        normalized.append(
            {
                "description": description,
                "category": category,
                "amount": amount,
            }
        )

    return normalized


def sum_expenses(expenses):
    return sum((expense["amount"] for expense in expenses), Decimal("0.00")).quantize(
        MONEY_QUANT,
        rounding=ROUND_HALF_UP,
    )


def percentage(part, total):
    if total <= 0:
        return Decimal("0.00")

    return ((part / total) * Decimal("100")).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def as_float(value):
    return float(value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP))


def calculate_summary(salary, fixed_expenses=None, variable_expenses=None):
    salary_amount = to_decimal(salary)
    fixed_items = normalize_expenses(fixed_expenses)
    variable_items = normalize_expenses(variable_expenses)

    fixed_total = sum_expenses(fixed_items)
    variable_total = sum_expenses(variable_items)
    total_expenses = (fixed_total + variable_total).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
    remaining_balance = (salary_amount - total_expenses).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)

    committed_percentage = percentage(total_expenses, salary_amount)
    available_percentage = percentage(remaining_balance, salary_amount) if salary_amount > 0 else Decimal("0.00")

    chart_balance = remaining_balance if remaining_balance > 0 else Decimal("0.00")

    return {
        "salary": as_float(salary_amount),
        "fixed_expenses": [
            {
                "description": item["description"],
                "category": item["category"],
                "amount": as_float(item["amount"]),
            }
            for item in fixed_items
        ],
        "variable_expenses": [
            {
                "description": item["description"],
                "category": item["category"],
                "amount": as_float(item["amount"]),
            }
            for item in variable_items
        ],
        "fixed_total": as_float(fixed_total),
        "variable_total": as_float(variable_total),
        "total_expenses": as_float(total_expenses),
        "remaining_balance": as_float(remaining_balance),
        "committed_percentage": as_float(committed_percentage),
        "available_percentage": as_float(available_percentage),
        "is_over_budget": remaining_balance < 0,
        "has_salary": salary_amount > 0,
        "chart": {
            "labels": ["Gastos fixos", "Gastos variados", "Saldo restante"],
            "values": [
                as_float(fixed_total),
                as_float(variable_total),
                as_float(chart_balance),
            ],
        },
    }
