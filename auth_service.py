from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password_hash, password):
    if not password_hash or not password:
        return False

    return check_password_hash(password_hash, password)
