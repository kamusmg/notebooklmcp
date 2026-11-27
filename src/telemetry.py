"""Local usage telemetry — privacy-friendly, nothing sent externally.

Data stored in ~/.notebooklmcp/telemetry.json. User can delete at any time.
"""
import json
import logging
import time
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

_TELEMETRY_FILE = Path.home() / ".notebooklmcp" / "telemetry.json"


class UsageTracker:
    def __init__(self, path: Path = _TELEMETRY_FILE) -> None:
        self._path = path
        self._counts: dict = defaultdict(int)
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._counts.update(json.loads(self._path.read_text(encoding="utf-8")))
            except Exception as e:
                logger.warning("Could not load telemetry: %s", e)

    def track(self, operation: str) -> None:
        self._counts[operation] += 1
        self._counts[f"{operation}_last_ts"] = int(time.time())
        self._save()

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps(dict(self._counts), indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("Could not save telemetry: %s", e)

    def report(self) -> dict:
        return dict(self._counts)


tracker = UsageTracker()
