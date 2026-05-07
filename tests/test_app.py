import unittest
import tempfile
import re
from pathlib import Path
from unittest.mock import patch

import auth_routes
import app as app_module
from app import app
from auth_service import hash_password
from init_db import initialize_database
from repositories import SQLiteBudgetRepository


class AppTest(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        auth_routes.auth_rate_limiter.clear()

    def get_csrf_token(self):
        response = self.client.get("/")
        match = re.search(rb'name="csrf-token" content="([^"]+)"', response.data)

        self.assertIsNotNone(match)

        return match.group(1).decode()

    def csrf_headers(self):
        return {"X-CSRF-Token": self.get_csrf_token()}

    def create_test_user(self, database_path, name):
        repository = SQLiteBudgetRepository(database_path)
        try:
            repository.init_schema()
            return repository.create_user(name, hash_password("senha-segura"))
        finally:
            repository.close()

    def set_session_user(self, user):
        with self.client.session_transaction() as session:
            session["user_id"] = user.id
            session["user_name"] = user.name

    def test_index_loads(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["Referrer-Policy"], "same-origin")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])
        self.assertIn("https://cdn.jsdelivr.net", response.headers["Content-Security-Policy"])
        self.assertIn("Gestão Financeira".encode(), response.data)
        self.assertIn(b"financeChart", response.data)
        self.assertIn(b'<meta name="app-version" content="1.1">', response.data)
        self.assertIn(b'name="csrf-token"', response.data)
        self.assertIn(b"Login", response.data)
        self.assertIn("Mês".encode(), response.data)
        self.assertIn(b"Ano", response.data)
        self.assertIn(b"Salvar", response.data)
        self.assertNotIn(b'id="loadBudgetButton"', response.data)
        self.assertIn(b"Duplicar anterior", response.data)
        self.assertIn(b'aria-live="polite"', response.data)
        self.assertIn(b'id="feedbackPopup"', response.data)
        self.assertIn(b"Fechar aviso", response.data)
        self.assertIn(b"Meses salvos", response.data)
        self.assertIn(b'id="savedMonthsList"', response.data)
        self.assertIn(b"Entre meses", response.data)
        self.assertIn("Histórico mensal".encode(), response.data)
        self.assertIn(b"Gerenciar", response.data)
        self.assertIn(b'id="saveStateIndicator"', response.data)
        self.assertIn(b'id="categoryGoalInput"', response.data)
        self.assertIn(b'id="categoryGoalsList"', response.data)
        self.assertIn(b"Valores e metas por categoria", response.data)
        self.assertIn(b'id="fixedCategoryOptions"', response.data)
        self.assertIn(b'id="variableCategoryOptions"', response.data)
        self.assertIn(b'autocomplete="off"', response.data)

    def test_login_form_loads(self):
        response = self.client.get("/login")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Acesso opcional", response.data)
        self.assertIn(b"Continuar sem login", response.data)
        self.assertIn(b"Criar conta", response.data)
        self.assertIn(b"Confirmar senha", response.data)

    def test_404_page_loads(self):
        response = self.client.get("/pagina-inexistente")

        self.assertEqual(response.status_code, 404)
        self.assertIn("Página não encontrada".encode(), response.data)

    def test_login_with_local_user(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"
            initialize_database(database_path)
            csrf_token = self.get_csrf_token()

            with patch.object(auth_routes, "DATABASE_PATH", database_path):
                response = self.client.post(
                    "/login",
                    data={"name": "Usuário local", "password": "local", "csrf_token": csrf_token},
                    follow_redirects=True,
                )

            self.assertEqual(response.status_code, 200)
            self.assertIn("Usuário local".encode(), response.data)
            self.assertIn(b"Sair", response.data)

    def test_invalid_login_shows_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"
            initialize_database(database_path)
            csrf_token = self.get_csrf_token()

            with patch.object(auth_routes, "DATABASE_PATH", database_path):
                response = self.client.post(
                    "/login",
                    data={"name": "Usuário local", "password": "senha-errada", "csrf_token": csrf_token},
                )

            self.assertEqual(response.status_code, 401)
            self.assertIn("Usuário ou senha inválidos.".encode(), response.data)

    def test_login_rate_limit_blocks_repeated_failures(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"
            initialize_database(database_path)
            csrf_token = self.get_csrf_token()

            with patch.object(auth_routes, "DATABASE_PATH", database_path):
                responses = [
                    self.client.post(
                        "/login",
                        data={"name": "Usuário local", "password": "senha-errada", "csrf_token": csrf_token},
                    )
                    for _ in range(6)
                ]

            self.assertEqual([response.status_code for response in responses[:5]], [401, 401, 401, 401, 401])
            self.assertEqual(responses[5].status_code, 429)
            self.assertIn("Muitas tentativas".encode(), responses[5].data)

    def test_idle_session_expires_user(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["user_name"] = "Usuário local"
            session["_last_seen_at"] = 1

        with patch.object(app_module, "SESSION_IDLE_TIMEOUT_SECONDS", 1):
            response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Login", response.data)
        self.assertNotIn(b"Sair", response.data)

    def test_register_creates_user_and_logs_in(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"
            csrf_token = self.get_csrf_token()

            with patch.object(auth_routes, "DATABASE_PATH", database_path):
                response = self.client.post(
                    "/register",
                    data={
                        "name": "Nova conta",
                        "password": "senha-segura",
                        "password_confirmation": "senha-segura",
                        "csrf_token": csrf_token,
                    },
                    follow_redirects=True,
                )

            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Nova conta", response.data)
            self.assertIn(b"Sair", response.data)

    def test_register_rejects_existing_user(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"
            initialize_database(database_path)
            csrf_token = self.get_csrf_token()

            with patch.object(auth_routes, "DATABASE_PATH", database_path):
                first_response = self.client.post(
                    "/register",
                    data={
                        "name": "Usuário local",
                        "password": "senha-segura",
                        "password_confirmation": "senha-segura",
                        "csrf_token": csrf_token,
                    },
                )

            self.assertEqual(first_response.status_code, 409)
            self.assertIn("Este usuário já existe.".encode(), first_response.data)

    def test_register_requires_matching_password_confirmation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"
            csrf_token = self.get_csrf_token()

            with patch.object(auth_routes, "DATABASE_PATH", database_path):
                response = self.client.post(
                    "/register",
                    data={
                        "name": "Nova conta",
                        "password": "senha-segura",
                        "password_confirmation": "outra",
                        "csrf_token": csrf_token,
                    },
                )

            self.assertEqual(response.status_code, 400)
            self.assertIn("A confirmação de senha não confere.".encode(), response.data)

    def test_register_requires_minimum_password_length(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"
            csrf_token = self.get_csrf_token()

            with patch.object(auth_routes, "DATABASE_PATH", database_path):
                response = self.client.post(
                    "/register",
                    data={
                        "name": "Nova conta",
                        "password": "curta",
                        "password_confirmation": "curta",
                        "csrf_token": csrf_token,
                    },
                )

            self.assertEqual(response.status_code, 400)
            self.assertIn(b"A senha deve ter pelo menos 8 caracteres.", response.data)

    def test_register_rate_limit_blocks_repeated_failures(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"
            csrf_token = self.get_csrf_token()

            with patch.object(auth_routes, "DATABASE_PATH", database_path):
                responses = [
                    self.client.post(
                        "/register",
                        data={
                            "name": "Nova conta",
                            "password": "curta",
                            "password_confirmation": "curta",
                            "csrf_token": csrf_token,
                        },
                    )
                    for _ in range(6)
                ]

            self.assertEqual([response.status_code for response in responses[:5]], [400, 400, 400, 400, 400])
            self.assertEqual(responses[5].status_code, 429)
            self.assertIn("Muitas tentativas".encode(), responses[5].data)

    def test_logout_keeps_index_available(self):
        csrf_token = self.get_csrf_token()
        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["user_name"] = "Usuário local"

        response = self.client.post("/logout", data={"csrf_token": csrf_token}, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Gestão Financeira".encode(), response.data)
        self.assertIn(b"Login", response.data)

    def test_summary_endpoint(self):
        response = self.client.post(
            "/api/summary",
            json={
                "salary": "3500,00",
                "fixed_expenses": [{"description": "Aluguel", "category": "Casa", "amount": "1200,00"}],
                "variable_expenses": [{"description": "Mercado", "category": "Alimentacao", "amount": "450,00"}],
            },
        )

        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["total_expenses"], 1650.00)
        self.assertEqual(data["remaining_balance"], 1850.00)
        self.assertEqual(data["fixed_expenses"][0]["category"], "Casa")
        self.assertFalse(data["is_over_budget"])

    def test_summary_endpoint_over_budget(self):
        response = self.client.post(
            "/api/summary",
            json={
                "salary": "1000,00",
                "fixed_expenses": [{"description": "Aluguel", "amount": "900,00"}],
                "variable_expenses": [{"description": "Compra", "amount": "250,00"}],
            },
        )

        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["remaining_balance"], -150.00)
        self.assertTrue(data["is_over_budget"])
        self.assertEqual(data["chart"]["values"], [900.00, 250.00, 0.00])

    def test_save_and_load_month_budget_without_required_login(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"

            with patch.object(app_module, "DATABASE_PATH", database_path):
                headers = self.csrf_headers()
                save_response = self.client.post(
                    "/api/month-budget",
                    headers=headers,
                    json={
                        "month": 5,
                        "year": 2026,
                        "salary": "3500,00",
                        "fixed_expenses": [
                            {"description": "Aluguel", "category": "Moradia", "amount": "1200,00"}
                        ],
                        "variable_expenses": [
                            {"description": "Mercado", "category": "Alimentacao", "amount": "450,00"}
                        ],
                    },
                )
                load_response = self.client.get("/api/month-budget?month=5&year=2026")

            saved_data = save_response.get_json()
            loaded_data = load_response.get_json()

            self.assertEqual(save_response.status_code, 200)
            self.assertTrue(saved_data["saved"])
            self.assertEqual(saved_data["salary"], 3500.00)
            self.assertEqual(load_response.status_code, 200)
            self.assertTrue(loaded_data["found"])
            self.assertEqual(loaded_data["fixed_expenses"][0]["category"], "Moradia")
            self.assertEqual(loaded_data["variable_expenses"][0]["amount"], 450.00)

    def test_load_month_budget_not_found(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"

            with patch.object(app_module, "DATABASE_PATH", database_path):
                response = self.client.get("/api/month-budget?month=5&year=2026")

            data = response.get_json()

            self.assertEqual(response.status_code, 200)
            self.assertFalse(data["found"])

    def test_export_month_budget_csv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"

            with patch.object(app_module, "DATABASE_PATH", database_path):
                headers = self.csrf_headers()
                self.client.post(
                    "/api/month-budget",
                    headers=headers,
                    json={
                        "month": 5,
                        "year": 2026,
                        "salary": "3500,00",
                        "fixed_expenses": [
                            {"description": "Aluguel", "category": "Moradia", "amount": "1200,00"}
                        ],
                        "variable_expenses": [
                            {"description": "Mercado", "category": "Alimentacao", "amount": "450,00"}
                        ],
                    },
                )
                response = self.client.get("/api/month-budget/export?month=5&year=2026")

            csv_text = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("text/csv", response.content_type)
            self.assertIn("orcamento-2026-05.csv", response.headers["Content-Disposition"])
            self.assertIn("mes;ano;salario;tipo;descricao;categoria;valor", csv_text)
            self.assertIn("5;2026;3500.00;fixo;Aluguel;Moradia;1200.00", csv_text)

    def test_delete_month_budget_endpoint(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"

            with patch.object(app_module, "DATABASE_PATH", database_path):
                headers = self.csrf_headers()
                self.client.post(
                    "/api/month-budget",
                    headers=headers,
                    json={"month": 5, "year": 2026, "salary": "3500,00"},
                )
                delete_response = self.client.post(
                    "/api/month-budget/delete",
                    headers=headers,
                    json={"month": 5, "year": 2026},
                )
                load_response = self.client.get("/api/month-budget?month=5&year=2026")

            self.assertEqual(delete_response.status_code, 200)
            self.assertTrue(delete_response.get_json()["deleted"])
            self.assertFalse(load_response.get_json()["found"])

    def test_month_budget_data_is_isolated_by_user(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"
            user_a = self.create_test_user(database_path, "Usuario A")
            user_b = self.create_test_user(database_path, "Usuario B")
            headers = self.csrf_headers()

            with patch.object(app_module, "DATABASE_PATH", database_path):
                self.set_session_user(user_a)
                save_response = self.client.post(
                    "/api/month-budget",
                    headers=headers,
                    json={
                        "month": 5,
                        "year": 2026,
                        "salary": "3500,00",
                        "fixed_expenses": [
                            {"description": "Aluguel", "category": "Moradia", "amount": "1200,00"}
                        ],
                    },
                )

                self.set_session_user(user_b)
                load_response = self.client.get("/api/month-budget?month=5&year=2026")
                list_response = self.client.get("/api/month-budgets")
                export_response = self.client.get("/api/month-budget/export?month=5&year=2026")
                delete_response = self.client.post(
                    "/api/month-budget/delete",
                    headers=headers,
                    json={"month": 5, "year": 2026},
                )

                self.set_session_user(user_a)
                owner_load_response = self.client.get("/api/month-budget?month=5&year=2026")

            self.assertEqual(save_response.status_code, 200)
            self.assertTrue(save_response.get_json()["saved"])
            self.assertEqual(load_response.status_code, 200)
            self.assertFalse(load_response.get_json()["found"])
            self.assertEqual(list_response.get_json()["month_budgets"], [])
            self.assertEqual(export_response.status_code, 404)
            self.assertEqual(delete_response.status_code, 404)
            self.assertTrue(owner_load_response.get_json()["found"])

    def test_list_month_budgets_returns_saved_months_with_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"

            with patch.object(app_module, "DATABASE_PATH", database_path):
                headers = self.csrf_headers()
                self.client.post(
                    "/api/month-budget",
                    headers=headers,
                    json={
                        "month": 5,
                        "year": 2026,
                        "salary": "3500,00",
                        "fixed_expenses": [
                            {"description": "Aluguel", "category": "Moradia", "amount": "1200,00"}
                        ],
                        "variable_expenses": [
                            {"description": "Mercado", "category": "Alimentacao", "amount": "450,00"}
                        ],
                    },
                )
                self.client.post(
                    "/api/month-budget",
                    headers=headers,
                    json={
                        "month": 6,
                        "year": 2026,
                        "salary": "4200,00",
                        "fixed_expenses": [
                            {"description": "Financiamento", "category": "Casa", "amount": "1500,00"}
                        ],
                        "variable_expenses": [
                            {"description": "Viagem", "category": "Lazer", "amount": "900,00"}
                        ],
                    },
                )
                response = self.client.get("/api/month-budgets")

            data = response.get_json()
            budgets = data["month_budgets"]

            self.assertEqual(response.status_code, 200)
            self.assertEqual([(budget["month"], budget["year"]) for budget in budgets], [(6, 2026), (5, 2026)])
            self.assertEqual(budgets[0]["salary"], 4200.00)
            self.assertEqual(budgets[0]["total_expenses"], 2400.00)
            self.assertEqual(budgets[0]["remaining_balance"], 1800.00)
            self.assertFalse(budgets[0]["is_over_budget"])

    def test_create_and_list_categories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"

            with patch.object(app_module, "DATABASE_PATH", database_path):
                headers = self.csrf_headers()
                create_response = self.client.post(
                    "/api/categories",
                    headers=headers,
                    json={"name": "Moradia", "type": "fixed", "goal_amount": "1200,00"},
                )
                list_response = self.client.get("/api/categories")

            create_data = create_response.get_json()
            list_data = list_response.get_json()

            self.assertEqual(create_response.status_code, 200)
            self.assertTrue(create_data["created"])
            self.assertEqual(create_data["category"]["name"], "Moradia")
            self.assertEqual(create_data["category"]["goal_amount"], 1200.00)
            self.assertEqual(list_response.status_code, 200)
            self.assertEqual(list_data["categories"][0]["type"], "fixed")
            self.assertEqual(list_data["categories"][0]["goal_amount"], 1200.00)

    def test_create_category_rejects_duplicate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"

            with patch.object(app_module, "DATABASE_PATH", database_path):
                headers = self.csrf_headers()
                self.client.post("/api/categories", headers=headers, json={"name": "Lazer", "type": "variable"})
                duplicate_response = self.client.post(
                    "/api/categories",
                    headers=headers,
                    json={"name": "Lazer", "type": "variable"},
                )

            data = duplicate_response.get_json()

            self.assertEqual(duplicate_response.status_code, 409)
            self.assertFalse(data["created"])

    def test_update_and_delete_category(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"

            with patch.object(app_module, "DATABASE_PATH", database_path):
                headers = self.csrf_headers()
                create_response = self.client.post(
                    "/api/categories",
                    headers=headers,
                    json={"name": "Casa", "type": "fixed"},
                )
                category_id = create_response.get_json()["category"]["id"]
                update_response = self.client.post(
                    f"/api/categories/{category_id}/update",
                    headers=headers,
                    json={"name": "Moradia", "type": "both", "goal_amount": "900,50"},
                )
                delete_response = self.client.post(
                    f"/api/categories/{category_id}/delete",
                    headers=headers,
                )
                list_response = self.client.get("/api/categories")

            update_data = update_response.get_json()
            list_data = list_response.get_json()

            self.assertEqual(update_response.status_code, 200)
            self.assertTrue(update_data["updated"])
            self.assertEqual(update_data["category"]["name"], "Moradia")
            self.assertEqual(update_data["category"]["type"], "both")
            self.assertEqual(update_data["category"]["goal_amount"], 900.50)
            self.assertEqual(delete_response.status_code, 200)
            self.assertEqual(list_data["categories"], [])

    def test_category_patch_and_delete_methods_still_work(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"

            with patch.object(app_module, "DATABASE_PATH", database_path):
                headers = self.csrf_headers()
                create_response = self.client.post(
                    "/api/categories",
                    headers=headers,
                    json={"name": "Casa", "type": "fixed"},
                )
                category_id = create_response.get_json()["category"]["id"]
                update_response = self.client.patch(
                    f"/api/categories/{category_id}",
                    headers=headers,
                    json={"name": "Moradia", "type": "variable"},
                )
                delete_response = self.client.delete(
                    f"/api/categories/{category_id}",
                    headers=headers,
                )

            self.assertEqual(update_response.status_code, 200)
            self.assertEqual(update_response.get_json()["category"]["type"], "variable")
            self.assertEqual(delete_response.status_code, 200)

    def test_categories_are_isolated_by_user(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"
            user_a = self.create_test_user(database_path, "Usuario A")
            user_b = self.create_test_user(database_path, "Usuario B")
            headers = self.csrf_headers()

            with patch.object(app_module, "DATABASE_PATH", database_path):
                self.set_session_user(user_a)
                create_response = self.client.post(
                    "/api/categories",
                    headers=headers,
                    json={"name": "Moradia", "type": "fixed", "goal_amount": "1200,00"},
                )
                category_id = create_response.get_json()["category"]["id"]

                self.set_session_user(user_b)
                list_response = self.client.get("/api/categories")
                update_response = self.client.post(
                    f"/api/categories/{category_id}/update",
                    headers=headers,
                    json={"name": "Lazer", "type": "variable"},
                )
                delete_response = self.client.post(
                    f"/api/categories/{category_id}/delete",
                    headers=headers,
                )

                self.set_session_user(user_a)
                owner_list_response = self.client.get("/api/categories")

            self.assertEqual(create_response.status_code, 200)
            self.assertEqual(list_response.get_json()["categories"], [])
            self.assertEqual(update_response.status_code, 404)
            self.assertEqual(delete_response.status_code, 404)
            self.assertEqual(len(owner_list_response.get_json()["categories"]), 1)

    def test_api_rejects_mutation_without_csrf_token(self):
        response = self.client.post("/api/categories", json={"name": "Moradia", "type": "fixed"})
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("Sessão expirada", data["message"])

    def test_month_budget_rejects_invalid_period(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"

            with patch.object(app_module, "DATABASE_PATH", database_path):
                headers = self.csrf_headers()
                invalid_month_response = self.client.post(
                    "/api/month-budget",
                    headers=headers,
                    json={"month": 13, "year": 2026, "salary": "1000,00"},
                )
                invalid_year_response = self.client.get("/api/month-budget?month=5&year=1899")

            self.assertEqual(invalid_month_response.status_code, 400)
            self.assertIn("mês entre 1 e 12", invalid_month_response.get_json()["message"])
            self.assertEqual(invalid_year_response.status_code, 400)
            self.assertIn("ano entre 1900 e 9999", invalid_year_response.get_json()["message"])

    def test_save_and_load_different_month_budgets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"

            with patch.object(app_module, "DATABASE_PATH", database_path):
                headers = self.csrf_headers()
                may_save_response = self.client.post(
                    "/api/month-budget",
                    headers=headers,
                    json={
                        "month": 5,
                        "year": 2026,
                        "salary": "3500,00",
                        "fixed_expenses": [
                            {"description": "Aluguel", "category": "Moradia", "amount": "1200,00"}
                        ],
                        "variable_expenses": [
                            {"description": "Mercado", "category": "Alimentacao", "amount": "450,00"}
                        ],
                    },
                )
                june_save_response = self.client.post(
                    "/api/month-budget",
                    headers=headers,
                    json={
                        "month": 6,
                        "year": 2026,
                        "salary": "4200,00",
                        "fixed_expenses": [
                            {"description": "Financiamento", "category": "Casa", "amount": "1500,00"}
                        ],
                        "variable_expenses": [
                            {"description": "Viagem", "category": "Lazer", "amount": "900,00"}
                        ],
                    },
                )
                may_load_response = self.client.get("/api/month-budget?month=5&year=2026")
                june_load_response = self.client.get("/api/month-budget?month=6&year=2026")

            may_data = may_load_response.get_json()
            june_data = june_load_response.get_json()

            self.assertEqual(may_save_response.status_code, 200)
            self.assertEqual(june_save_response.status_code, 200)
            self.assertEqual(may_data["salary"], 3500.00)
            self.assertEqual(may_data["fixed_expenses"][0]["description"], "Aluguel")
            self.assertEqual(may_data["variable_expenses"][0]["amount"], 450.00)
            self.assertEqual(june_data["salary"], 4200.00)
            self.assertEqual(june_data["fixed_expenses"][0]["description"], "Financiamento")
            self.assertEqual(june_data["variable_expenses"][0]["amount"], 900.00)


if __name__ == "__main__":
    unittest.main()
