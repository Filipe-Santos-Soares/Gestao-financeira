from datetime import datetime

from flask import jsonify, Flask, render_template, request, session

from auth_routes import auth_bp
from auth_service import hash_password
from config import (
    CREATE_LOCAL_USER,
    DATABASE_BACKEND,
    DATABASE_PATH,
    DATABASE_URL,
    IS_PRODUCTION,
    LOCAL_USER_NAME,
    LOCAL_USER_PASSWORD,
    SECRET_KEY,
    validate_runtime_config,
)
from finance_logic import calculate_summary
from repositories import PostgreSQLBudgetRepository, SQLiteBudgetRepository


validate_runtime_config()
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
APP_VERSION = "1.0"
app.register_blueprint(auth_bp)


def get_current_period(payload=None):
    payload = payload or {}
    now = datetime.now()

    month = int(payload.get("month") or request.args.get("month") or now.month)
    year = int(payload.get("year") or request.args.get("year") or now.year)

    return month, year


def get_repository():
    if DATABASE_BACKEND == "postgresql":
        repository = PostgreSQLBudgetRepository(DATABASE_URL)
    else:
        repository = SQLiteBudgetRepository(DATABASE_PATH)

    repository.init_schema()
    return repository


def get_active_user(repository):
    user_id = session.get("user_id")

    if user_id:
        user = repository.get_user(user_id)

        if user:
            return user

    if CREATE_LOCAL_USER:
        return repository.get_or_create_user(
            LOCAL_USER_NAME,
            hash_password(LOCAL_USER_PASSWORD),
        )

    return None


def no_active_user_response():
    return jsonify({"message": "Crie uma conta ou faca login para usar esta acao."}), 401


def expense_to_dict(expense):
    return {
        "description": expense.description,
        "category": expense.category,
        "amount": float(expense.amount),
    }


def category_to_dict(category):
    return {
        "id": category.id,
        "name": category.name,
        "type": category.type,
    }


def budget_response(budget, fixed_expenses, variable_expenses):
    return {
        "month": budget.month,
        "year": budget.year,
        "salary": float(budget.salary),
        "fixed_expenses": [expense_to_dict(expense) for expense in fixed_expenses],
        "variable_expenses": [expense_to_dict(expense) for expense in variable_expenses],
    }


def month_budget_list_item(repository, budget):
    fixed_expenses = repository.list_expenses(budget.id, "fixed")
    variable_expenses = repository.list_expenses(budget.id, "variable")
    fixed_expense_dicts = [expense_to_dict(expense) for expense in fixed_expenses]
    variable_expense_dicts = [expense_to_dict(expense) for expense in variable_expenses]
    summary = calculate_summary(
        salary=budget.salary,
        fixed_expenses=fixed_expense_dicts,
        variable_expenses=variable_expense_dicts,
    )

    return {
        "month": budget.month,
        "year": budget.year,
        "salary": float(budget.salary),
        "fixed_total": summary["fixed_total"],
        "variable_total": summary["variable_total"],
        "total_expenses": summary["total_expenses"],
        "remaining_balance": summary["remaining_balance"],
        "is_over_budget": summary["is_over_budget"],
        "updated_at": budget.updated_at,
    }


@app.get("/")
def index():
    return render_template(
        "index.html",
        app_version=APP_VERSION,
        current_user_name=session.get("user_name"),
    )


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", title="Pagina nao encontrada", message="A pagina solicitada nao existe."), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("error.html", title="Erro interno", message="Nao foi possivel concluir a acao agora."), 500


@app.post("/api/summary")
def summary():
    payload = request.get_json(silent=True) or {}

    result = calculate_summary(
        salary=payload.get("salary", 0),
        fixed_expenses=payload.get("fixed_expenses", []),
        variable_expenses=payload.get("variable_expenses", []),
    )

    return jsonify(result)


@app.get("/api/categories")
def list_categories():
    repository = get_repository()

    try:
        user = get_active_user(repository)
        if not user:
            return no_active_user_response()

        categories = repository.list_categories(user.id)

        return jsonify({"categories": [category_to_dict(category) for category in categories]})
    finally:
        repository.close()


@app.post("/api/categories")
def create_category():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    category_type = str(payload.get("type", "both")).strip() or "both"

    if category_type not in {"fixed", "variable", "both"}:
        return jsonify({"created": False, "message": "Tipo de categoria invalido."}), 400

    if not name:
        return jsonify({"created": False, "message": "Informe o nome da categoria."}), 400

    repository = get_repository()

    try:
        user = get_active_user(repository)
        if not user:
            return no_active_user_response()

        existing_category = repository.get_category_by_name_and_type(user.id, name, category_type)

        if existing_category:
            return (
                jsonify(
                    {
                        "created": False,
                        "message": "Esta categoria ja existe.",
                        "category": category_to_dict(existing_category),
                    }
                ),
                409,
            )

        category = repository.create_category(user.id, name, category_type)

        return jsonify({"created": True, "category": category_to_dict(category)})
    finally:
        repository.close()


@app.get("/api/month-budgets")
def list_month_budgets():
    repository = get_repository()

    try:
        user = get_active_user(repository)
        if not user:
            return no_active_user_response()

        budgets = repository.list_month_budgets(user.id)

        return jsonify(
            {
                "month_budgets": [
                    month_budget_list_item(repository, budget) for budget in budgets
                ]
            }
        )
    finally:
        repository.close()


@app.get("/api/month-budget")
def load_month_budget():
    month, year = get_current_period()
    repository = get_repository()

    try:
        user = get_active_user(repository)
        if not user:
            return no_active_user_response()

        budget = repository.get_month_budget(user.id, month, year)

        if not budget:
            return jsonify(
                {
                    "found": False,
                    "month": month,
                    "year": year,
                    "message": "Nenhum orcamento salvo para este mes.",
                }
            )

        fixed_expenses = repository.list_expenses(budget.id, "fixed")
        variable_expenses = repository.list_expenses(budget.id, "variable")
        data = budget_response(budget, fixed_expenses, variable_expenses)
        data["found"] = True

        return jsonify(data)
    finally:
        repository.close()


@app.post("/api/month-budget")
def save_month_budget():
    payload = request.get_json(silent=True) or {}
    month, year = get_current_period(payload)
    salary = payload.get("salary", 0)
    fixed_expenses = payload.get("fixed_expenses", [])
    variable_expenses = payload.get("variable_expenses", [])

    repository = get_repository()

    try:
        user = get_active_user(repository)
        if not user:
            return no_active_user_response()

        budget = repository.get_or_create_month_budget(user.id, month, year, salary)
        budget = repository.update_month_budget_salary(budget.id, salary)
        repository.replace_expenses(budget.id, fixed_expenses, variable_expenses)

        saved_fixed_expenses = repository.list_expenses(budget.id, "fixed")
        saved_variable_expenses = repository.list_expenses(budget.id, "variable")
        data = budget_response(budget, saved_fixed_expenses, saved_variable_expenses)
        data["saved"] = True

        return jsonify(data)
    finally:
        repository.close()


if __name__ == "__main__":
    app.run(debug=not IS_PRODUCTION, use_reloader=False)
