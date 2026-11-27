"""Anonymize fixture files by replacing real IDs with generic placeholders."""
import re
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "responses"

# Patterns: (regex, placeholder)
REPLACEMENTS = [
    # UUID notebook/task IDs
    (r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', 'NOTEBOOK_ID_PLACEHOLDER'),
    # Numeric task IDs (long numbers that appear as strings in JSON)
    (r'"task_id"\s*:\s*"(\d{10,})"', '"task_id": "TASK_ID_PLACEHOLDER"'),
    # Source IDs in JSON arrays (typically short alphanumeric strings after notebook UUID)
    (r'"source_id"\s*:\s*"([^"]{8,})"', '"source_id": "SOURCE_ID_PLACEHOLDER"'),
    # Artifact IDs
    (r'"artifact_id"\s*:\s*"([^"]{8,})"', '"artifact_id": "ARTIFACT_ID_PLACEHOLDER"'),
    # Email addresses
    (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 'USER_EMAIL_PLACEHOLDER'),
    # Google user IDs (numeric, 20+ digits)
    (r'\b\d{18,21}\b', 'GOOGLE_USER_ID_PLACEHOLDER'),
]


def anonymize_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    original = text
    for pattern, placeholder in REPLACEMENTS:
        text = re.sub(pattern, placeholder, text)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return 1
    return 0


def main() -> None:
    if not FIXTURES_DIR.exists():
        print(f"No fixtures dir found: {FIXTURES_DIR}")
        sys.exit(0)

    files = list(FIXTURES_DIR.glob("*.txt"))
    if not files:
        print("No .txt fixture files found.")
        sys.exit(0)

    changed = sum(anonymize_file(f) for f in files)
    print(f"Anonymized {changed}/{len(files)} files in {FIXTURES_DIR}")


if __name__ == "__main__":
    main()
