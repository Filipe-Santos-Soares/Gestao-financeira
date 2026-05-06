from flask import Blueprint, redirect, render_template, request, session, url_for

from auth_service import hash_password, verify_password
from config import DATABASE_BACKEND, DATABASE_PATH, DATABASE_URL
from repositories import PostgreSQLBudgetRepository, SQLiteBudgetRepository


auth_bp = Blueprint("auth", __name__)


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

    repository = get_auth_repository()
    try:
        user = repository.get_user_by_name(name)
    finally:
        repository.close()

    if not user or not verify_password(user.password_hash, password):
        return render_login(error="Usuário ou senha inválidos."), 401

    session["user_id"] = user.id
    session["user_name"] = user.name

    return redirect(url_for("index"))


@auth_bp.post("/register")
def register():
    name = request.form.get("name", "").strip()
    password = request.form.get("password", "")
    password_confirmation = request.form.get("password_confirmation", "")

    if not name or not password:
        return render_login(register_error="Informe usuário e senha para criar a conta."), 400

    if len(name) < 3:
        return render_login(register_error="O usuário deve ter pelo menos 3 caracteres."), 400

    if len(password) < 8:
        return render_login(register_error="A senha deve ter pelo menos 8 caracteres."), 400

    if password != password_confirmation:
        return render_login(register_error="A confirmação de senha não confere."), 400

    repository = get_auth_repository()
    try:
        existing_user = repository.get_user_by_name(name)

        if existing_user:
            return render_login(register_error="Este usuário já existe. Escolha outro nome."), 409

        user = repository.create_user(name, hash_password(password))
    finally:
        repository.close()

    session["user_id"] = user.id
    session["user_name"] = user.name

    return redirect(url_for("index"))


@auth_bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
