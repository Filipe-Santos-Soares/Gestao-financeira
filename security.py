import time
from secrets import compare_digest, token_urlsafe

from flask import request, session


CSRF_SESSION_KEY = "_csrf_token"
SESSION_LAST_SEEN_KEY = "_last_seen_at"


class RateLimiter:
    def __init__(self, attempts, window_seconds, clock=None):
        self.attempts = attempts
        self.window_seconds = window_seconds
        self.clock = clock or time.time
        self._attempts = {}

    def _prune(self, key, now):
        window_start = now - self.window_seconds
        attempts = [timestamp for timestamp in self._attempts.get(key, []) if timestamp > window_start]

        if attempts:
            self._attempts[key] = attempts
        else:
            self._attempts.pop(key, None)

        return attempts

    def is_limited(self, key):
        if self.attempts <= 0:
            return False

        return len(self._prune(key, self.clock())) >= self.attempts

    def record_failure(self, key):
        if self.attempts <= 0:
            return

        now = self.clock()
        attempts = self._prune(key, now)
        attempts.append(now)
        self._attempts[key] = attempts

    def reset(self, key):
        self._attempts.pop(key, None)

    def clear(self):
        self._attempts.clear()


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


def get_client_ip():
    forwarded_for = request.headers.get("X-Forwarded-For", "")

    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()

    return request.remote_addr or "unknown"


def rate_limit_key(action, identifier=""):
    return f"{action}:{get_client_ip()}:{str(identifier).strip().lower()}"


def refresh_session_activity(idle_timeout_seconds):
    now = int(time.time())
    last_seen = session.get(SESSION_LAST_SEEN_KEY)

    try:
        last_seen_at = int(last_seen) if last_seen else None
    except (TypeError, ValueError):
        last_seen_at = None

    if last_seen_at and now - last_seen_at > idle_timeout_seconds:
        session.clear()
        session.permanent = True
        session[SESSION_LAST_SEEN_KEY] = now
        return False

    session.permanent = True
    session[SESSION_LAST_SEEN_KEY] = now

    return True
