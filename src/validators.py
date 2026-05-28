"""Input validators for MCP tool parameters."""
import re

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def validate_notebook_id(nb_id: str) -> None:
    if not nb_id or not isinstance(nb_id, str):
        raise ValueError("notebook_id is required (string)")
    if not _UUID_RE.match(nb_id.strip()):
        raise ValueError(f"notebook_id must be a UUID (8-4-4-4-12 format). Got: '{nb_id[:60]}'")


def validate_url(url: str, field: str = "url") -> None:
    if not url or not isinstance(url, str):
        raise ValueError(f"{field} is required")
    if not url.startswith(("https://", "http://", "git@")):
        raise ValueError(f"{field} must start with https://, http://, or git@. Got: '{url[:80]}'")


def validate_question(question: str, min_len: int = 3) -> None:
    if not question or len(question.strip()) < min_len:
        raise ValueError(f"question must have at least {min_len} characters")


def validate_mode(mode: str, valid: tuple = ("fast", "deep")) -> None:
    if mode.lower() not in valid:
        raise ValueError(f"mode must be one of {valid}. Got: '{mode}'")


def validate_artifact_type(artifact_type: str) -> None:
    valid = ("study_guide", "briefing_doc", "blog_post", "quiz", "slide_deck", "data_table", "custom")
    if artifact_type.lower() not in valid:
        raise ValueError(f"artifact_type must be one of {valid}. Got: '{artifact_type}'")
