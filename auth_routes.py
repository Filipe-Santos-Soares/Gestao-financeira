from flask import Blueprint, redirect, render_template, request, session, url_for

from auth_service import hash_password, verify_password
from config import AUTH_RATE_LIMIT_ATTEMPTS, AUTH_RATE_LIMIT_WINDOW_SECONDS, DATABASE_BACKEND, DATABASE_PATH, DATABASE_URL
from repositories import PostgreSQLBudgetRepository, SQLiteBudgetRepository
from security import RateLimiter, rate_limit_key


auth_bp = Blueprint("auth", __name__)
auth_rate_limiter = RateLimiter(AUTH_RATE_LIMIT_ATTEMPTS, AUTH_RATE_LIMIT_WINDOW_SECONDS)


def get_auth_repository():
    if DATABASE_BACKEND == "postgresql":
        repository = PostgreSQLBudgetRepository(DATABASE_URL)
    else:
        repository = SQLiteBudgetRepository(DATABASE_PATH)

    repository.init_schema()
    return repository


def render_login(error=None, register_error=None):
    return render_template(
        "login.html",
        error=error,
        register_error=register_error,
    )


def rate_limited_message():
    return "Muitas tentativas em pouco tempo. Aguarde alguns minutos e tente novamente."


def get_current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    repository = get_auth_repository()
    try:
        return repository.get_user(user_id)
    finally:
        repository.close()


@auth_bp.get("/login")
def login_form():
    if get_current_user():
        return redirect(url_for("index"))

    return render_login()


@auth_bp.post("/login")
def login():
    name = request.form.get("name", "").strip()
    password = request.form.get("password", "")
    limiter_key = rate_limit_key("login", name)

    if auth_rate_limiter.is_limited(limiter_key):
        return render_login(error=rate_limited_message()), 429

    repository = get_auth_repository()
    try:
        user = repository.get_user_by_name(name)
    finally:
        repository.close()

    if not user or not verify_password(user.password_hash, password):
        auth_rate_limiter.record_failure(limiter_key)
        return render_login(error="Usuário ou senha inválidos."), 401

    auth_rate_limiter.reset(limiter_key)
    session.clear()
    session.permanent = True
    session["user_id"] = user.id
    session["user_name"] = user.name

    return redirect(url_for("index"))


@auth_bp.post("/register")
def register():
    name = request.form.get("name", "").strip()
    password = request.form.get("password", "")
    password_confirmation = request.form.get("password_confirmation", "")
    limiter_key = rate_limit_key("register", name)

    if auth_rate_limiter.is_limited(limiter_key):
        return render_login(register_error=rate_limited_message()), 429

    if not name or not password:
        auth_rate_limiter.record_failure(limiter_key)
        return render_login(register_error="Informe usuário e senha para criar a conta."), 400

    if len(name) < 3:
        auth_rate_limiter.record_failure(limiter_key)
        return render_login(register_error="O usuário deve ter pelo menos 3 caracteres."), 400

    if len(password) < 8:
        auth_rate_limiter.record_failure(limiter_key)
        return render_login(register_error="A senha deve ter pelo menos 8 caracteres."), 400

    if password != password_confirmation:
        auth_rate_limiter.record_failure(limiter_key)
        return render_login(register_error="A confirmação de senha não confere."), 400

    repository = get_auth_repository()
    try:
        existing_user = repository.get_user_by_name(name)

        if existing_user:
            auth_rate_limiter.record_failure(limiter_key)
            return render_login(register_error="Este usuário já existe. Escolha outro nome."), 409

        user = repository.create_user(name, hash_password(password))
    finally:
        repository.close()

    auth_rate_limiter.reset(limiter_key)
    session.clear()
    session.permanent = True
    session["user_id"] = user.id
    session["user_name"] = user.name

    return redirect(url_for("index"))


@auth_bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
