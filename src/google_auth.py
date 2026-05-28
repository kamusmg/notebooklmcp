import os
import re
import logging
from typing import TypedDict, Tuple, Optional
from curl_cffi.requests import AsyncSession
from dotenv import load_dotenv
from src.exceptions import AuthExpiredError, CaptchaRequiredError

load_dotenv()

logger = logging.getLogger(__name__)

class AuthTokens(TypedDict):
    cookies: str
    csrf_token: str
    build_label: str

def get_google_cookies() -> dict[str, str]:
    """Retrieves Google auth cookies from environment variables."""
    raw_cookies = os.getenv("GOOGLE_COOKIES")
    if raw_cookies:
        cookies = {}
        for item in raw_cookies.split(";"):
            if "=" in item:
                k, v = item.split("=", 1)
                cookies[k.strip()] = v.strip()
        return cookies

    sid = os.getenv("GOOGLE_SID")
    hsid = os.getenv("GOOGLE_HSID")
    ssid = os.getenv("GOOGLE_SSID")
    papisid = os.getenv("GOOGLE_3PAPISID")

    # Filter out empty or placeholder values
    cookies = {}
    if sid and not sid.startswith("COPIE_"):
        cookies["SID"] = sid
    if hsid and not hsid.startswith("COPIE_"):
        cookies["HSID"] = hsid
    if ssid and not ssid.startswith("COPIE_"):
        cookies["SSID"] = ssid
    if papisid and not papisid.startswith("COPIE_"):
        cookies["__Secure-3PAPISID"] = papisid

    return cookies

def format_cookie_header(cookies: dict[str, str]) -> str:
    """Formats the cookies dictionary into a single Cookie header string."""
    return "; ".join(f"{k}={v}" for k, v in cookies.items())

def parse_cookies_string(cookie_header: str) -> dict[str, str]:
    cookies = {}
    for item in cookie_header.split(";"):
        if "=" in item:
            k, v = item.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies

def create_http_client(cookie_header: str) -> AsyncSession:
    """Creates a configured curl_cffi AsyncSession that impersonates Chrome 131.

    Uses BoringSSL TLS stack matching real Chrome (JA3/JA4 indistinguishable from
    a real browser), plus all SACRED headers required for Google's RPC same-origin
    bypass. Cookies are loaded from GOOGLE_COOKIES_B64 (preserves domain metadata)
    with a fallback to the flat cookie header string.
    """
    import base64
    import json

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://notebooklm.google.com",
        "Referer": "https://notebooklm.google.com/",
        "X-Goog-AuthUser": "0",
        "X-Same-Domain": "1",  # Crucial bypass header for Google RPC
        "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }
    client = AsyncSession(
        headers=headers,
        timeout=120.0,
        impersonate="chrome131",
        allow_redirects=True,
    )

    # First try to load full cookies with domains and paths (preserves subdomains mapping)
    cookies_b64 = os.getenv("GOOGLE_COOKIES_B64")
    if cookies_b64:
        try:
            cookies_json = base64.b64decode(cookies_b64.encode('utf-8')).decode('utf-8')
            cookies_list = json.loads(cookies_json)
            for c in cookies_list:
                domain = c.get("domain", "")
                client.cookies.set(c["name"], c["value"], domain=domain, path=c.get("path", "/"))
            return client
        except Exception as e:
            logger.error(f"Failed to load GOOGLE_COOKIES_B64: {e}")

    # Fallback to standard cookie parsing
    cookies_dict = parse_cookies_string(cookie_header)
    for k, v in cookies_dict.items():
        client.cookies.set(k, v, domain=".google.com")
    return client

async def refresh_at_and_bl(client: AsyncSession) -> Tuple[str, str]:
    """Scrapes notebooklm.google.com to extract the CSRF ('at') token and build label ('bl')."""
    try:
        response = await client.get("https://notebooklm.google.com/")

        if response.status_code in (401, 403) or "accounts.google.com" in str(response.url):
            raise AuthExpiredError(
                "Google cookies expired. Run authenticate() to renew."
            )

        if "support.google.com/accounts" in str(response.url):
            raise AuthExpiredError(
                "Google redirected to support page (cookies likely expired). Run authenticate() to renew."
            )

        if response.status_code != 200:
            raise RuntimeError(f"Failed to access NotebookLM homepage. Status: {response.status_code}")

        html = response.text

        if "Please verify you're human" in html or "captcha" in html.lower()[:2000]:
            raise CaptchaRequiredError(
                "Google requires CAPTCHA. Run authenticate() to complete manual login."
            )

        # Extract CSRF ('at') token — SACRED: regex name "SNlM0e" is reverse-engineered
        at_match = re.search(r'"SNlM0e":"([^"]+)"', html)
        if not at_match:
            raise ValueError("Could not find Google CSRF 'at' token in page source. Please verify your cookies.")
        csrf_token = at_match.group(1)

        # Extract Build Label ('bl') — SACRED: regex name "cfb2h" is reverse-engineered
        bl_match = re.search(r'"cfb2h":"([^"]+)"', html)
        if bl_match:
            build_label = bl_match.group(1)
        else:
            bl_match_fallback = re.search(r'"bl":"([^"]+)"', html)
            if bl_match_fallback:
                build_label = bl_match_fallback.group(1)
            else:
                build_label = "boq_labs-tailwind-frontend_20260121.08_p0"

        logger.info("Successfully authenticated and retrieved CSRF token and build label.")
        return csrf_token, build_label

    except (AuthExpiredError, CaptchaRequiredError):
        raise
    except Exception as e:
        logger.error(f"Error during Google authentication/scraping: {str(e)}")
        raise
