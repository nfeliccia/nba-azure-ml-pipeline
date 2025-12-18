"""Utilities for warming up Azure SQL serverless connections."""

from __future__ import annotations

from typing import Callable

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, OperationalError
from tenacity import RetryError, retry, retry_if_exception, stop_after_attempt, wait_exponential

RESUME_ERROR_CODES = {40613}
RESUME_SUBSTRINGS = {
    "not currently available",
    "is not configured to accept connections",
}


def _should_retry(exc: BaseException) -> bool:
    if isinstance(exc, RetryError):
        return False
    if isinstance(exc, OperationalError):
        return _matches_resume(exc)
    if isinstance(exc, DBAPIError):
        return _matches_resume(exc)
    return False


def _matches_resume(exc: DBAPIError) -> bool:
    orig = exc.orig
    message = str(exc)

    if hasattr(orig, "args") and orig.args:
        code = getattr(orig.args[0], "get", lambda *_: None)("SQLSTATE") if isinstance(orig.args[0], dict) else None
        if isinstance(orig.args[0], int) and orig.args[0] in RESUME_ERROR_CODES:
            return True
        if isinstance(orig.args[0], dict) and orig.args[0].get("code") in RESUME_ERROR_CODES:
            return True
        if isinstance(orig.args[0], (list, tuple)) and orig.args[0][0] in RESUME_ERROR_CODES:
            return True
        if code in RESUME_ERROR_CODES:
            return True
    return any(fragment.lower() in message.lower() for fragment in RESUME_SUBSTRINGS)


def _warmup_call(engine: Engine) -> None:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


warmup: Callable[[Engine], None] = retry(
    retry=retry_if_exception(_should_retry),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    stop=stop_after_attempt(5),
)(_warmup_call)
