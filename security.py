from secrets import compare_digest, token_urlsafe

from flask import request, session


CSRF_SESSION_KEY = "_csrf_token"


def get_csrf_token():
    token = session.get(CSRF_SESSION_KEY)

    if not token:
        token = token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token

    return token


def get_request_csrf_token():
    return request.headers.get("X-CSRF-Token") or request.form.get("csrf_token", "")


def is_valid_csrf_token(token):
    session_token = session.get(CSRF_SESSION_KEY)

    if not token or not session_token:
        return False

    return compare_digest(session_token, token)
