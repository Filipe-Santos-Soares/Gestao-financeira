import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
DEFAULT_DATABASE_PATH = DATABASE_DIR / "app.db"
ENVIRONMENT = os.environ.get("APP_ENV", "development").lower()
IS_PRODUCTION = ENVIRONMENT == "production"
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

DATABASE_BACKEND = "postgresql" if DATABASE_URL.startswith(("postgres://", "postgresql://")) else "sqlite"
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", DEFAULT_DATABASE_PATH))
DEFAULT_SECRET_KEY = "dev-secret-key-change-before-deploy"
SECRET_KEY = os.environ.get("SECRET_KEY", DEFAULT_SECRET_KEY)

LOCAL_USER_NAME = os.environ.get("LOCAL_USER_NAME", "Usuário local")
LOCAL_USER_PASSWORD = os.environ.get("LOCAL_USER_PASSWORD", "local")
CREATE_LOCAL_USER = os.environ.get("CREATE_LOCAL_USER", "true").lower() in {"1", "true", "yes"}
SESSION_IDLE_TIMEOUT_SECONDS = int(os.environ.get("SESSION_IDLE_TIMEOUT_SECONDS", "7200"))
AUTH_RATE_LIMIT_ATTEMPTS = int(os.environ.get("AUTH_RATE_LIMIT_ATTEMPTS", "5"))
AUTH_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("AUTH_RATE_LIMIT_WINDOW_SECONDS", "900"))


def validate_runtime_config():
    if IS_PRODUCTION and SECRET_KEY == DEFAULT_SECRET_KEY:
        raise RuntimeError("Defina SECRET_KEY antes de executar em produção.")
