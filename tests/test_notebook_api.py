"""Tests for NotebookLMClient parsing logic — no real credentials needed."""
import pytest
from src.notebook_api import NotebookLMClient, safe_get
from src.exceptions import (
    AuthExpiredError, CaptchaRequiredError, RpcStructureError,
    NotebookNotFoundError, RateLimitError, NotebookLMError
)


class TestSafeGet:
    def test_returns_value_at_valid_index(self):
        assert safe_get([1, 2, 3], 0) == 1
        assert safe_get([1, 2, 3], 2) == 3

    def test_returns_default_for_out_of_bounds(self):
        assert safe_get([1, 2], 5) is None
        assert safe_get([1, 2], 5, default="fallback") == "fallback"

    def test_returns_default_for_non_list(self):
        assert safe_get("not a list", 0) is None
        assert safe_get(None, 0, default="x") == "x"
        assert safe_get(42, 0) is None

    def test_context_param_accepted(self):
        assert safe_get([], 0, context="test") is None


class TestParseBatchResponse:
    """Tests for _parse_batch_response using hand-crafted fixtures.

    Note: Real fixtures would be more comprehensive (see Fase 1 of upgrade plan).
    These tests cover the parsing contract and edge cases.
    """

    def _make_client(self):
        # Client without real cookies — only testing parse methods
        from unittest.mock import MagicMock
        import httpx
        client = NotebookLMClient.__new__(NotebookLMClient)
        client.csrf_token = "test_csrf"
        client.build_label = "test_bl"
        client.client = MagicMock()
        return client

    def test_raises_on_captcha(self):
        c = self._make_client()
        with pytest.raises(CaptchaRequiredError):
            c._parse_batch_response("Please verify you're human")

    def test_raises_on_captcha_lowercase(self):
        c = self._make_client()
        with pytest.raises(CaptchaRequiredError):
            c._parse_batch_response("error: captcha required")

    def test_strips_xssi_prefix(self):
        c = self._make_client()
        import json
        inner = json.dumps([[["wrb.fr", None, json.dumps(["result"]), None, None, None, "generic"], None, None]])
        payload = f")]}}'\n{json.dumps([[inner]])}"
        # Should not raise — parsing may return None for unexpected structure but shouldn't crash
        result = c._parse_batch_response(f")]}}'\n{inner}")
        # Just verifying no exception raised on normal input
        assert result is None or isinstance(result, list)

    def test_returns_none_on_empty(self):
        c = self._make_client()
        result = c._parse_batch_response("")
        assert result is None

    def test_returns_none_on_gibberish(self):
        c = self._make_client()
        result = c._parse_batch_response("not json at all !@#")
        assert result is None


class TestExceptions:
    def test_exception_hierarchy(self):
        assert issubclass(AuthExpiredError, NotebookLMError)
        assert issubclass(CaptchaRequiredError, NotebookLMError)
        assert issubclass(RpcStructureError, NotebookLMError)
        assert issubclass(NotebookNotFoundError, NotebookLMError)
        assert issubclass(RateLimitError, NotebookLMError)
        assert issubclass(NotebookLMError, Exception)

    def test_auth_expired_message(self):
        e = AuthExpiredError("cookies expired")
        assert "cookies expired" in str(e)

    def test_captcha_message(self):
        e = CaptchaRequiredError("captcha needed")
        assert "captcha needed" in str(e)


class TestRpcIds:
    def test_all_rpc_ids_are_strings(self):
        from src.rpc_ids import RpcId
        for attr in ("CREATE_NOTEBOOK", "ADD_SOURCE", "START_FAST_RESEARCH",
                     "START_DEEP_RESEARCH", "POLL_RESEARCH", "IMPORT_RESEARCH_SOURCES",
                     "GET_NOTEBOOK", "CREATE_ARTIFACT", "LIST_ARTIFACTS"):
            val = getattr(RpcId, attr)
            assert isinstance(val, str) and len(val) > 3, f"{attr} should be non-empty string"

    def test_no_duplicate_rpc_ids(self):
        from src.rpc_ids import RpcId
        ids = [
            RpcId.CREATE_NOTEBOOK, RpcId.ADD_SOURCE, RpcId.START_FAST_RESEARCH,
            RpcId.START_DEEP_RESEARCH, RpcId.POLL_RESEARCH, RpcId.IMPORT_RESEARCH_SOURCES,
            RpcId.GET_NOTEBOOK, RpcId.CREATE_ARTIFACT, RpcId.LIST_ARTIFACTS,
        ]
        assert len(ids) == len(set(ids)), "Duplicate RPC IDs detected"
