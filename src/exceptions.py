"""Typed exceptions for NotebookLM MCP server."""


class NotebookLMError(Exception):
    """Base exception for NotebookLM errors."""


class AuthExpiredError(NotebookLMError):
    """Google cookies have expired or are invalid. Run authenticate()."""


class CaptchaRequiredError(NotebookLMError):
    """Google requires CAPTCHA. Manual browser login needed."""


class RpcStructureError(NotebookLMError):
    """RPC response has unexpected structure (Google may have changed the API)."""


class NotebookNotFoundError(NotebookLMError):
    """Notebook ID does not exist or user has no access."""


class RateLimitError(NotebookLMError):
    """Google returned 429 or equivalent rate limit response."""
