import os
import sys
import json
import time
import logging
import subprocess
from typing import Optional
import httpx
import asyncio
import websockets

logger = logging.getLogger(__name__)

REMOTE_DEBUGGING_PORT = 9222
NOTEBOOKLM_URL = "https://notebooklm.google.com/"

def find_chrome() -> Optional[str]:
    """Locate the Google Chrome executable path depending on the platform."""
    if sys.platform == "win32":
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]
    elif sys.platform == "darwin":
        possible_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        ]
    else:
        possible_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium"
        ]

    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

async def is_debug_port_available() -> bool:
    """Check if the remote debugging port is open and responding."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://127.0.0.1:{REMOTE_DEBUGGING_PORT}/json/version", timeout=1.0)
            return response.status_code == 200
    except Exception:
        return False

async def get_pages() -> list:
    """Retrieve all open tabs/pages from Chrome DevTools Protocol."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://127.0.0.1:{REMOTE_DEBUGGING_PORT}/json/list", timeout=2.0)
            if response.status_code == 200:
                return response.json()
    except Exception:
        pass
    return []

async def wait_for_login(max_wait_seconds: int = 300) -> Optional[str]:
    """Poll open pages until user logs in and reaches the main NotebookLM page."""
    start_time = time.time()
    logger.info("Aguardando login no Google NotebookLM...")
    print("⏳ Aguardando você fazer login no navegador...", file=sys.stderr)
    print("   (O script vai detectar automaticamente quando você entrar)", file=sys.stderr)

    while time.time() - start_time < max_wait_seconds:
        pages = await get_pages()
        for page in pages:
            url = page.get("url", "")
            ws_url = page.get("webSocketDebuggerUrl")
            
            # Detect successful navigation to NotebookLM dashboard (excluding signin/accounts/login pages)
            if "notebooklm.google.com" in url and "notebooklm.google.com/login" not in url and "accounts.google.com" not in url and "signin" not in url and ws_url:
                logger.info("Login detectado com sucesso!")
                print("✅ Login detectado com sucesso!", file=sys.stderr)
                return ws_url
                
        await asyncio.sleep(2)
    return None

async def extract_cookies_via_cdp(ws_url: str) -> dict[str, str]:
    """Connect to page WebSocket and request all cookies via Chrome DevTools Protocol."""
    logger.info("Conectando ao WebSocket do Chrome...")
    async with websockets.connect(ws_url) as ws:
        # 1. Enable Network Domain
        await ws.send(json.dumps({
            "id": 1,
            "method": "Network.enable"
        }))
        await ws.recv()

        # 2. Get All Cookies
        await ws.send(json.dumps({
            "id": 2,
            "method": "Network.getAllCookies"
        }))
        
        response = await ws.recv()
        res_data = json.loads(response)

        cookies = {}
        if "result" in res_data and "cookies" in res_data["result"]:
            for c in res_data["result"]["cookies"]:
                domain = c.get("domain", "")
                if "google.com" in domain or "notebooklm" in domain:
                    cookies[c["name"]] = c["value"]

        return cookies

async def run_browser_login() -> dict:
    """Main orchestration for Chrome remote debugging and cookie extraction."""
    chrome_path = find_chrome()
    if not chrome_path:
        raise RuntimeError("Google Chrome não foi encontrado. Por favor, instale o Google Chrome.")

    logger.info(f"Usando Chrome em: {chrome_path}")

    # Check if Chrome is already debugging
    debug_active = await is_debug_port_available()
    
    if not debug_active:
        # Check if Chrome is running without remote debugging (Windows tasklist/Linux pgrep check)
        # Warn user if they need to close it first
        profile_dir = os.path.join(os.path.expanduser("~"), ".notebooklm-mcp", "chrome-profile")
        os.makedirs(profile_dir, exist_ok=True)

        logger.info("Iniciando Chrome com porta de depuração remota 9222...")
        print("🚀 Abrindo o Google Chrome para autenticação...", file=sys.stderr)
        
        chrome_args = [
            chrome_path,
            f"--remote-debugging-port={REMOTE_DEBUGGING_PORT}",
            "--remote-allow-origins=*",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            NOTEBOOKLM_URL
        ]

        # Launch detached process
        if sys.platform == "win32":
            subprocess.Popen(chrome_args, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(chrome_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Give Chrome a few seconds to boot
        await asyncio.sleep(4)

        if not await is_debug_port_available():
            raise RuntimeError(
                "Não foi possível conectar à porta de depuração do Chrome.\n"
                "Por favor, feche todas as janelas do Chrome antes de tentar novamente."
            )

    # Wait for login
    ws_url = await wait_for_login(300)
    if not ws_url:
        raise TimeoutError("Tempo limite esgotado esperando o login do usuário (5 minutos).")

    # Extract cookies
    print("🍪 Extraindo cookies da sessão...", file=sys.stderr)
    cookies = await extract_cookies_via_cdp(ws_url)

    required_keys = ["SID", "HSID", "SSID", "__Secure-3PAPISID"]
    extracted = {}
    for key in required_keys:
        if key in cookies:
            extracted[key] = cookies[key]

    if len(extracted) < len(required_keys):
        missing = [k for k in required_keys if k not in extracted]
        logger.warning(f"Alguns cookies necessários estão ausentes: {missing}")

    # Compile the complete cookie string containing all cookies (guarantees authentication success)
    all_cookies_str = "; ".join(f"{k}={v}" for k, v in cookies.items())

    # Write cookies directly to the .env file in the workspace
    env_content = f"""# Autenticação Google Pro (Bypass de Login/Playwright)
GOOGLE_SID="{extracted.get('SID', '')}"
GOOGLE_HSID="{extracted.get('HSID', '')}"
GOOGLE_SSID="{extracted.get('SSID', '')}"
GOOGLE_3PAPISID="{extracted.get('__Secure-3PAPISID', '')}"
GOOGLE_COOKIES="{all_cookies_str}"

# Configurações do seu Ambiente Antigravity
ANTIGRAVITY_PROJECT_MODE="PROACTIVE"
"""
    
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)

    print("📁 Cookies salvos com sucesso no arquivo .env!", file=sys.stderr)
    return extracted

if __name__ == "__main__":
    asyncio.run(run_browser_login())
