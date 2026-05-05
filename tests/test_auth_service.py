import unittest

from auth_service import hash_password, verify_password


class AuthServiceTest(unittest.TestCase):
    def test_hash_and_verify_password(self):
        password_hash = hash_password("senha-segura")

        self.assertNotEqual(password_hash, "senha-segura")
        self.assertTrue(verify_password(password_hash, "senha-segura"))
        self.assertFalse(verify_password(password_hash, "senha-errada"))


if __name__ == "__main__":
    unittest.main()
