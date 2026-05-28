"""Status code constants for Google NotebookLM RPC responses (reverse-engineered)."""
from typing import Optional


class ResearchStatus:
    IN_PROGRESS = 1
    COMPLETED_A = 2
    COMPLETED_B = 6  # alternate completed state observed in practice


class ArtifactStatus:
    PROCESSING = 1
    PENDING = 2
    COMPLETED = 3
    FAILED = 4


def parse_research_status(code: Optional[int]) -> str:
    if code in (ResearchStatus.COMPLETED_A, ResearchStatus.COMPLETED_B):
        return "completed"
    if code == ResearchStatus.IN_PROGRESS or code is None:
        return "in_progress"
    return "failed"


def parse_artifact_status(code: Optional[int]) -> str:
    if code == ArtifactStatus.COMPLETED:
        return "completed"
    if code in (ArtifactStatus.PROCESSING, ArtifactStatus.PENDING):
        return "in_progress"
    return "failed"
