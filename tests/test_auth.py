"""Tests for google_auth module — no real credentials needed."""
import pytest
from src.google_auth import parse_cookies_string, format_cookie_header, get_google_cookies


class TestParseCookiesString:
    def test_basic_parsing(self):
        result = parse_cookies_string("SID=abc; HSID=def; SSID=ghi")
        assert result == {"SID": "abc", "HSID": "def", "SSID": "ghi"}

    def test_strips_whitespace(self):
        result = parse_cookies_string("  SID = abc ; HSID = def ")
        assert result["SID"] == "abc"
        assert result["HSID"] == "def"

    def test_value_with_equals(self):
        result = parse_cookies_string("token=abc=def=ghi")
        assert result["token"] == "abc=def=ghi"

    def test_empty_string(self):
        result = parse_cookies_string("")
        assert result == {}

    def test_single_cookie(self):
        result = parse_cookies_string("SID=only_one")
        assert result == {"SID": "only_one"}


class TestFormatCookieHeader:
    def test_formats_cookies(self):
        result = format_cookie_header({"SID": "abc", "HSID": "def"})
        assert "SID=abc" in result
        assert "HSID=def" in result

    def test_single_cookie(self):
        result = format_cookie_header({"SID": "myvalue"})
        assert result == "SID=myvalue"

    def test_empty_dict(self):
        result = format_cookie_header({})
        assert result == ""


class TestGetGoogleCookies:
    def test_filters_placeholder_values(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_SID", "COPIE_O_VALOR_AQUI")
        monkeypatch.setenv("GOOGLE_HSID", "real_value_hsid")
        monkeypatch.delenv("GOOGLE_COOKIES", raising=False)
        monkeypatch.delenv("GOOGLE_SSID", raising=False)
        monkeypatch.delenv("GOOGLE_3PAPISID", raising=False)

        cookies = get_google_cookies()
        assert "SID" not in cookies
        assert cookies.get("HSID") == "real_value_hsid"

    def test_prefers_google_cookies_env(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_COOKIES", "SID=from_env; HSID=val2")
        cookies = get_google_cookies()
        assert cookies.get("SID") == "from_env"
        assert cookies.get("HSID") == "val2"

    def test_empty_when_no_cookies(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_COOKIES", raising=False)
        monkeypatch.delenv("GOOGLE_SID", raising=False)
        monkeypatch.delenv("GOOGLE_HSID", raising=False)
        monkeypatch.delenv("GOOGLE_SSID", raising=False)
        monkeypatch.delenv("GOOGLE_3PAPISID", raising=False)
        cookies = get_google_cookies()
        assert cookies == {}
