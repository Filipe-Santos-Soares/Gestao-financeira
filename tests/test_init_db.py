import tempfile
import unittest
from pathlib import Path

from auth_service import verify_password
from init_db import initialize_database
from repositories import SQLiteBudgetRepository


class InitDbTest(unittest.TestCase):
    def test_initialize_database_creates_schema_and_local_user(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"

            first_path, first_user = initialize_database(database_path)
            second_path, second_user = initialize_database(database_path)

            repository = SQLiteBudgetRepository(database_path)
            try:
                local_user = repository.get_user_by_name("Usuário local")
            finally:
                repository.close()

            self.assertEqual(first_path, database_path)
            self.assertEqual(second_path, database_path)
            self.assertEqual(first_user.id, second_user.id)
            self.assertEqual(local_user.name, "Usuário local")
            self.assertTrue(verify_password(local_user.password_hash, "local"))
            self.assertFalse(hasattr(local_user, "email"))


if __name__ == "__main__":
    unittest.main()
