"""Import cookies from Node.js notebooklm-mcp auth.json to Python project .env.

Usage:
    python scripts/import_cookies_from_node.py

The Node.js project stores cookies as a single string in:
    C:\\Users\\<user>\\.notebooklm-mcp\\auth.json

This script reads them and writes to the Python project's .env file.
"""
import json
import sys
from pathlib import Path

NODE_AUTH = Path.home() / ".notebooklm-mcp" / "auth.json"
PROJECT_ENV = Path(__file__).parent.parent / ".env"
ENV_EXAMPLE = Path(__file__).parent.parent / ".env.example"


def parse_cookie_string(cookie_str: str) -> dict:
    result = {}
    for item in cookie_str.split(";"):
        if "=" in item:
            k, v = item.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def main() -> int:
    if not NODE_AUTH.exists():
        print(f"ERROR: {NODE_AUTH} not found.")
        print("Run the Node.js notebooklm-mcp project first to generate auth.json.")
        return 1

    try:
        data = json.loads(NODE_AUTH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: Could not parse {NODE_AUTH}: {e}")
        return 1

    cookie_str = data.get("cookies", "")
    if not cookie_str:
        print(f"ERROR: 'cookies' key not found or empty in {NODE_AUTH}")
        return 1

    updated_at = data.get("updatedAt", "unknown")
    cookies = parse_cookie_string(cookie_str)

    sid = cookies.get("SID", "")
    hsid = cookies.get("HSID", "")
    ssid = cookies.get("SSID", "")
    papisid = cookies.get("__Secure-3PAPISID", "")

    if PROJECT_ENV.exists():
        existing = PROJECT_ENV.read_text(encoding="utf-8")
        if "GOOGLE_COOKIES=" in existing:
            print(f"WARNING: {PROJECT_ENV} already has GOOGLE_COOKIES set.")
            print("Overwriting with fresh cookies from auth.json...")

    env_content = f"""# Cookies imported from {NODE_AUTH}
# Source updated_at: {updated_at}
# IMPORTANT: never commit this file to git

GOOGLE_SID="{sid}"
GOOGLE_HSID="{hsid}"
GOOGLE_SSID="{ssid}"
GOOGLE_3PAPISID="{papisid}"
GOOGLE_COOKIES="{cookie_str}"
"""

    PROJECT_ENV.write_text(env_content, encoding="utf-8")
    print(f"[OK] Cookies imported to {PROJECT_ENV}")
    print(f"   SID: {sid[:20]}..." if sid else "   SID: (not found)")
    print(f"   HSID: {hsid[:20]}..." if hsid else "   HSID: (not found)")
    print(f"   {len(cookies)} cookies total imported")
    print(f"   Source date: {updated_at}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
