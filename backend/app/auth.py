"""Single-password authentication via a signed session cookie.

The whole app is for one user. We compare the submitted password against
APP_PASSWORD (env var) in constant time, and on success set an HTTP-only,
signed cookie. A SECRET_KEY env var signs the cookie; if absent we derive a
stable one from APP_PASSWORD (fine for a single-user tool, but set SECRET_KEY
in production for good measure).
"""
import hmac
import os
from fastapi import Request, HTTPException, Response
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

COOKIE_NAME = "jobtracker_session"
MAX_AGE = 60 * 60 * 24 * 30  # 30 days

APP_PASSWORD = os.environ.get("APP_PASSWORD", "changeme")
SECRET_KEY = os.environ.get("SECRET_KEY") or ("derived-" + APP_PASSWORD)

_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="jobtracker-auth")
_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "auto")


def check_password(submitted: str) -> bool:
    return hmac.compare_digest(submitted or "", APP_PASSWORD)


def issue_session(response: Response, request: Request):
    token = _serializer.dumps("authenticated")
    # Secure cookie when served over HTTPS (production). "auto" detects scheme.
    if _COOKIE_SECURE == "auto":
        secure = request.url.scheme == "https" or \
            request.headers.get("x-forwarded-proto", "").startswith("https")
    else:
        secure = _COOKIE_SECURE.lower() in ("1", "true", "yes")
    response.set_cookie(
        COOKIE_NAME, token, max_age=MAX_AGE, httponly=True,
        samesite="lax", secure=secure, path="/",
    )


def clear_session(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")


def is_authenticated(request: Request) -> bool:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return False
    try:
        _serializer.loads(token, max_age=MAX_AGE)
        return True
    except (BadSignature, SignatureExpired):
        return False


def require_auth(request: Request):
    """FastAPI dependency: raises 401 if not logged in."""
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return True
