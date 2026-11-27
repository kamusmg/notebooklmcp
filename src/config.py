"""Centralized configuration loaded from environment variables."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    http_timeout: float = float(os.getenv("NLM_HTTP_TIMEOUT", "120.0"))
    login_wait_seconds: int = int(os.getenv("NLM_LOGIN_WAIT", "300"))
    chrome_debug_port: int = int(os.getenv("NLM_CHROME_PORT", "9222"))
    # CSRF cache TTL — default 0 keeps existing per-call re-auth behavior (SACRED).
    # Set NLM_CSRF_TTL > 0 only after A/B testing confirms no CAPTCHA regression.
    csrf_cache_ttl_seconds: int = int(os.getenv("NLM_CSRF_TTL", "0"))
    capture_fixtures: bool = os.getenv("RTK_CAPTURE_FIXTURES") == "1"
    # When set, deep_query/poll_research/etc fall back to this notebook if caller omits notebook_id.
    default_notebook_id: str = os.getenv("DEFAULT_NOTEBOOK_ID", "")


settings = Settings()
