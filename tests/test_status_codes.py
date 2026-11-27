"""Tests for status_codes module — no real credentials needed."""
import pytest
from src.status_codes import parse_research_status, parse_artifact_status, ResearchStatus, ArtifactStatus


class TestParseResearchStatus:
    def test_in_progress(self):
        assert parse_research_status(ResearchStatus.IN_PROGRESS) == "in_progress"

    def test_completed_a(self):
        assert parse_research_status(ResearchStatus.COMPLETED_A) == "completed"

    def test_completed_b(self):
        assert parse_research_status(ResearchStatus.COMPLETED_B) == "completed"

    def test_none_is_in_progress(self):
        assert parse_research_status(None) == "in_progress"

    def test_unknown_code_is_failed(self):
        assert parse_research_status(99) == "failed"
        assert parse_research_status(0) == "failed"

    def test_all_known_codes(self):
        assert parse_research_status(1) == "in_progress"
        assert parse_research_status(2) == "completed"
        assert parse_research_status(6) == "completed"


class TestParseArtifactStatus:
    def test_processing(self):
        assert parse_artifact_status(ArtifactStatus.PROCESSING) == "in_progress"

    def test_pending(self):
        assert parse_artifact_status(ArtifactStatus.PENDING) == "in_progress"

    def test_completed(self):
        assert parse_artifact_status(ArtifactStatus.COMPLETED) == "completed"

    def test_failed(self):
        assert parse_artifact_status(ArtifactStatus.FAILED) == "failed"

    def test_none_is_failed(self):
        assert parse_artifact_status(None) == "failed"

    def test_unknown_code_is_failed(self):
        assert parse_artifact_status(99) == "failed"

    def test_all_known_codes(self):
        assert parse_artifact_status(1) == "in_progress"
        assert parse_artifact_status(2) == "in_progress"
        assert parse_artifact_status(3) == "completed"
        assert parse_artifact_status(4) == "failed"
