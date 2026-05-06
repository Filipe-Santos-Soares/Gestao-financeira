from auth_service import hash_password
from config import CREATE_LOCAL_USER, DATABASE_BACKEND, DATABASE_PATH, DATABASE_URL, LOCAL_USER_NAME, LOCAL_USER_PASSWORD
from repositories import PostgreSQLBudgetRepository, SQLiteBudgetRepository


def should_replace_local_password(password_hash):
    return password_hash == "local-user-placeholder"


def get_init_repository(database_path=DATABASE_PATH, database_url=DATABASE_URL):
    if DATABASE_BACKEND == "postgresql":
        return PostgreSQLBudgetRepository(database_url)

    return SQLiteBudgetRepository(database_path)


def initialize_database(database_path=DATABASE_PATH):
    repository = get_init_repository(database_path)
    local_user = None

    try:
        repository.init_schema()

        if CREATE_LOCAL_USER:
            secure_password_hash = hash_password(LOCAL_USER_PASSWORD)
            local_user = repository.get_or_create_user(
                LOCAL_USER_NAME,
                secure_password_hash,
            )

            if should_replace_local_password(local_user.password_hash):
                local_user = repository.update_user_password_hash(local_user.id, secure_password_hash)
    finally:
        repository.close()

    return database_path, local_user


if __name__ == "__main__":
    path, user = initialize_database()
    print(f"Banco inicializado em: {path}")

    if user:
        print(f"Usuário local: {user.name} (id={user.id})")
    else:
        print("Usuário local automático desativado.")
