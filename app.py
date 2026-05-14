import csv
from datetime import timedelta
from io import StringIO

from flask import jsonify, Flask, render_template, request, Response, session

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
    SESSION_IDLE_TIMEOUT_SECONDS,
    validate_runtime_config,
)
from finance_logic import calculate_summary
from repositories import PostgreSQLBudgetRepository, SQLiteBudgetRepository
from security import get_csrf_token, get_request_csrf_token, is_valid_csrf_token, refresh_session_activity
from validation import parse_period, parse_year, validate_category_payload, validate_month_budget_payload


validate_runtime_config()
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = IS_PRODUCTION
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(seconds=SESSION_IDLE_TIMEOUT_SECONDS)
APP_VERSION = "1.2"
app.register_blueprint(auth_bp)


def parse_current_period(payload=None):
    return parse_period(payload, request.args)


def parse_current_year(payload=None):
    return parse_year(payload, request.args)


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
    return jsonify({"message": "Sessão expirada ou acesso indisponível. Faça login para continuar."}), 401


def invalid_csrf_response():
    return jsonify({"message": "Sessão expirada. Recarregue a página e tente novamente."}), 400


@app.context_processor
def inject_csrf_token():
    return {"app_version": APP_VERSION, "csrf_token": get_csrf_token}


@app.before_request
def expire_idle_session():
    refresh_session_activity(SESSION_IDLE_TIMEOUT_SECONDS)


@app.before_request
def protect_state_changing_requests():
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return None

    if request.endpoint == "summary":
        return None

    if is_valid_csrf_token(get_request_csrf_token()):
        return None

    if request.path.startswith("/api/"):
        return invalid_csrf_response()

    return render_template("error.html", title="Sessão expirada", message="Recarregue a página e tente novamente."), 400


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()",
    )
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "font-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'; "
        "form-action 'self'",
    )

    return response


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
        "goal_amount": float(category.goal_amount) if category.goal_amount is not None else None,
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


def write_budget_expense_csv_rows(repository, writer, budget):
    fixed_expenses = repository.list_expenses(budget.id, "fixed")
    variable_expenses = repository.list_expenses(budget.id, "variable")

    for expense_type, expenses in (("fixo", fixed_expenses), ("variado", variable_expenses)):
        for expense in expenses:
            writer.writerow(
                [
                    budget.month,
                    budget.year,
                    f"{float(budget.salary):.2f}",
                    expense_type,
                    expense.description,
                    expense.category,
                    f"{float(expense.amount):.2f}",
                ]
            )


def csv_download_response(output, filename):
    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/")
def index():
    return render_template(
        "index.html",
        app_version=APP_VERSION,
        current_user_name=session.get("user_name"),
    )


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", title="Página não encontrada", message="A página solicitada não existe."), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("error.html", title="Erro interno", message="Não foi possível concluir a ação agora."), 500


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
    category_payload, validation_error = validate_category_payload(payload)

    if validation_error:
        return jsonify({"created": False, "message": validation_error}), 400

    name = category_payload["name"]
    category_type = category_payload["type"]
    goal_amount = category_payload["goal_amount"]

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
                        "message": "Esta categoria já existe.",
                        "category": category_to_dict(existing_category),
                    }
                ),
                409,
            )

        category = repository.create_category(user.id, name, category_type, goal_amount)

        return jsonify({"created": True, "category": category_to_dict(category)})
    finally:
        repository.close()


@app.patch("/api/categories/<int:category_id>")
@app.post("/api/categories/<int:category_id>/update")
def update_category(category_id):
    payload = request.get_json(silent=True) or {}
    category_payload, validation_error = validate_category_payload(payload)

    if validation_error:
        return jsonify({"updated": False, "message": validation_error}), 400

    name = category_payload["name"]
    category_type = category_payload["type"]
    goal_amount = category_payload["goal_amount"]

    repository = get_repository()

    try:
        user = get_active_user(repository)
        if not user:
            return no_active_user_response()

        category = repository.get_category(category_id)

        if not category or category.user_id != user.id:
            return jsonify({"updated": False, "message": "Categoria não encontrada."}), 404

        existing_category = repository.get_category_by_name_and_type(user.id, name, category_type)

        if existing_category and existing_category.id != category_id:
            return (
                jsonify(
                    {
                        "updated": False,
                        "message": "Esta categoria já existe.",
                        "category": category_to_dict(existing_category),
                    }
                ),
                409,
            )

        updated_category = repository.update_category(category_id, name, category_type, goal_amount)

        return jsonify({"updated": True, "category": category_to_dict(updated_category)})
    finally:
        repository.close()


@app.delete("/api/categories/<int:category_id>")
@app.post("/api/categories/<int:category_id>/delete")
def delete_category(category_id):
    repository = get_repository()

    try:
        user = get_active_user(repository)
        if not user:
            return no_active_user_response()

        category = repository.get_category(category_id)

        if not category or category.user_id != user.id:
            return jsonify({"deleted": False, "message": "Categoria não encontrada."}), 404

        deleted = repository.delete_category(category_id)

        return jsonify({"deleted": deleted})
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
    month, year, period_error = parse_current_period()

    if period_error:
        return jsonify({"found": False, "message": period_error}), 400

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
                    "message": "Nenhum orçamento salvo para este mês.",
                }
            )

        fixed_expenses = repository.list_expenses(budget.id, "fixed")
        variable_expenses = repository.list_expenses(budget.id, "variable")
        data = budget_response(budget, fixed_expenses, variable_expenses)
        data["found"] = True

        return jsonify(data)
    finally:
        repository.close()


@app.get("/api/month-budget/export")
def export_month_budget():
    month, year, period_error = parse_current_period()

    if period_error:
        return jsonify({"exported": False, "message": period_error}), 400

    repository = get_repository()

    try:
        user = get_active_user(repository)
        if not user:
            return no_active_user_response()

        budget = repository.get_month_budget(user.id, month, year)

        if not budget:
            return jsonify({"exported": False, "message": "Nenhum orçamento salvo para este mês."}), 404

        output = StringIO()
        writer = csv.writer(output, delimiter=";")
        writer.writerow(["mes", "ano", "salario", "tipo", "descricao", "categoria", "valor"])
        write_budget_expense_csv_rows(repository, writer, budget)

        filename = f"orcamento-{year}-{month:02d}.csv"

        return csv_download_response(output, filename)
    finally:
        repository.close()


@app.get("/api/year-budget/export")
def export_year_budget():
    year, year_error = parse_current_year()

    if year_error:
        return jsonify({"exported": False, "message": year_error}), 400

    repository = get_repository()

    try:
        user = get_active_user(repository)
        if not user:
            return no_active_user_response()

        budgets = [
            budget
            for budget in repository.list_month_budgets(user.id)
            if budget.year == year
        ]

        if not budgets:
            return jsonify({"exported": False, "message": "Nenhum orçamento salvo para este ano."}), 404

        output = StringIO()
        writer = csv.writer(output, delimiter=";")
        writer.writerow(["mes", "ano", "salario", "tipo", "descricao", "categoria", "valor"])

        for budget in sorted(budgets, key=lambda item: item.month):
            write_budget_expense_csv_rows(repository, writer, budget)

        return csv_download_response(output, f"orcamentos-{year}.csv")
    finally:
        repository.close()


@app.post("/api/month-budget")
def save_month_budget():
    payload = request.get_json(silent=True) or {}
    budget_payload, validation_error = validate_month_budget_payload(payload)

    if validation_error:
        return jsonify({"saved": False, "message": validation_error}), 400

    month = budget_payload["month"]
    year = budget_payload["year"]
    salary = budget_payload["salary"]
    fixed_expenses = budget_payload["fixed_expenses"]
    variable_expenses = budget_payload["variable_expenses"]

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


@app.post("/api/month-budget/delete")
def delete_month_budget():
    payload = request.get_json(silent=True) or {}
    month, year, period_error = parse_current_period(payload)

    if period_error:
        return jsonify({"deleted": False, "message": period_error}), 400

    repository = get_repository()

    try:
        user = get_active_user(repository)
        if not user:
            return no_active_user_response()

        deleted = repository.delete_month_budget(user.id, month, year)

        if not deleted:
            return jsonify({"deleted": False, "message": "Nenhum orçamento salvo para este mês."}), 404

        return jsonify({"deleted": True, "month": month, "year": year})
    finally:
        repository.close()


if __name__ == "__main__":
    app.run(debug=not IS_PRODUCTION, use_reloader=False)
