import os
import re
import logging
from typing import TypedDict, Tuple, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class AuthTokens(TypedDict):
    cookies: str
    csrf_token: str
    build_label: str

def get_google_cookies() -> dict[str, str]:
    """Retrieves Google auth cookies from environment variables."""
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

def create_http_client(cookie_header: str) -> httpx.AsyncClient:
    """Creates a configured httpx.AsyncClient with security-bypass headers."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://notebooklm.google.com",
        "Referer": "https://notebooklm.google.com/",
        "X-Goog-AuthUser": "0",
        "X-Same-Domain": "1",  # Crucial bypass header for Google RPC
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Cookie": cookie_header
    }
    return httpx.AsyncClient(headers=headers, timeout=30.0, follow_redirects=True)

async def refresh_at_and_bl(client: httpx.AsyncClient) -> Tuple[str, str]:
    """Scrapes notebooklm.google.com to extract the CSRF ('at') token and build label ('bl')."""
    try:
        response = await client.get("https://notebooklm.google.com/")
        if response.status_code != 200:
            raise RuntimeError(f"Failed to access NotebookLM homepage. Status: {response.status_code}")

        html = response.text

        # Extract CSRF ('at') token
        at_match = re.search(r'"SNlM0e":"([^"]+)"', html)
        if not at_match:
            raise ValueError("Could not find Google CSRF 'at' token in page source. Please verify your cookies.")
        csrf_token = at_match.group(1)

        # Extract Build Label ('bl')
        bl_match = re.search(r'"cfb2h":"([^"]+)"', html)
        if bl_match:
            build_label = bl_match.group(1)
        else:
            # Secondary fallback for bl
            bl_match_fallback = re.search(r'"bl":"([^"]+)"', html)
            if bl_match_fallback:
                build_label = bl_match_fallback.group(1)
            else:
                build_label = "boq_labs-tailwind-frontend_20260121.08_p0"  # Default fallback

        logger.info("Successfully authenticated and retrieved CSRF token and build label.")
        return csrf_token, build_label

    except Exception as e:
        logger.error(f"Error during Google authentication/scraping: {str(e)}")
        raise
