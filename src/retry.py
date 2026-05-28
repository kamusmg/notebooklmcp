"""Retry with exponential backoff for transient errors.

Only retries on:
- curl_cffi Timeout / ConnectionError (network glitches)
- HTTP 5xx
- HTTP 429 (rate limit, with larger delay)

Never retries on:
- AuthExpiredError, CaptchaRequiredError (won't improve with retry)
- HTTP 4xx (except 429)
"""
import asyncio
import logging
from typing import Callable, TypeVar, Awaitable

from curl_cffi.requests.exceptions import (
    Timeout,
    ConnectionError as CurlConnectionError,
    HTTPError,
)

from src.exceptions import AuthExpiredError, CaptchaRequiredError

logger = logging.getLogger(__name__)
T = TypeVar("T")


async def with_retry(
    func: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    base_delay: float = 1.0,
    factor: float = 2.0,
) -> T:
    last_exc: Exception = RuntimeError("No attempts made")
    for attempt in range(max_retries):
        try:
            return await func()
        except (AuthExpiredError, CaptchaRequiredError):
            raise  # Never retry auth failures
        except (Timeout, CurlConnectionError) as e:
            last_exc = e
            delay = base_delay * (factor ** attempt)
            logger.warning("Retry %d/%d after %.1fs — %s: %s", attempt + 1, max_retries, delay, type(e).__name__, e)
            await asyncio.sleep(delay)
        except HTTPError as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status == 429:
                delay = base_delay * (factor ** attempt) * 3  # larger backoff for rate limit
                logger.warning("Rate limit (429), retry after %.1fs", delay)
                await asyncio.sleep(delay)
                last_exc = e
            elif status is not None and 500 <= status < 600:
                delay = base_delay * (factor ** attempt)
                logger.warning("HTTP %d, retry after %.1fs", status, delay)
                await asyncio.sleep(delay)
                last_exc = e
            else:
                raise  # 4xx (non-429) or unknown status — don't retry
    raise last_exc
