import os
import sys
import logging
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Ensure the project root src directory is in Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.google_auth import get_google_cookies, format_cookie_header, refresh_at_and_bl
from src.notebook_api import NotebookLMClient

# Configure logging to stderr to prevent stdout corruption in JSON-RPC stdio transport
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("notebooklmcp-v2-server")

load_dotenv()

# Initialize FastMCP Server
mcp = FastMCP("notebooklmcp-v2-engine")

async def _get_authenticated_client() -> NotebookLMClient:
    """Helper to initialize and authenticate the NotebookLM Client."""
    cookies = get_google_cookies()
    if not cookies:
        raise ValueError(
            "Missing Google authentication cookies. "
            "Please configure GOOGLE_SID, GOOGLE_HSID, GOOGLE_SSID, and GOOGLE_3PAPISID in your .env file."
        )

    cookie_header = format_cookie_header(cookies)
    
    # Create a temporary client to perform token refresh
    from src.google_auth import create_http_client
    async with create_http_client(cookie_header) as temp_client:
        csrf_token, build_label = await refresh_at_and_bl(temp_client)

    return NotebookLMClient(
        cookies_header=cookie_header,
        csrf_token=csrf_token,
        build_label=build_label
    )

@mcp.tool()
async def provision_lifecycle(project_name: str, github_repo_url: str) -> Dict[str, Any]:
    """
    Creates an isolated Google NotebookLM notebook for the current project,
    links the GitHub repository URL as a primary source, and persists the
    notebook ID locally in '.notebook_id'.

    Parameters:
    - project_name: The name of the project folder in Antigravity.
    - github_repo_url: Public or private URL of the project's Git repository.
    """
    try:
        client = await _get_authenticated_client()
        
        # 1. Create the notebook
        title = f"AG-ENV: {project_name}"
        notebook_id = await client.create_notebook(title)
        
        # 2. Link Git Repository URL as source
        await client.add_source_url(notebook_id, github_repo_url)
        
        # 3. Persist ID in .notebook_id file at workspace root
        with open(".notebook_id", "w", encoding="utf-8") as f:
            f.write(notebook_id.strip())

        await client.close()
        
        return {
            "status": "success",
            "notebook_id": notebook_id,
            "message": f"NotebookLM environment '{title}' successfully provisioned and git source linked."
        }
    except Exception as e:
        logger.error(f"Error in provision_lifecycle: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@mcp.tool()
async def deep_query(notebook_id: str, question: str) -> Dict[str, Any]:
    """
    Sends a query directly to the chat interface of the specified NotebookLM notebook,
    returning the grounded synthesized response. Consumes zero local token quota.

    Parameters:
    - notebook_id: The ID of the NotebookLM notebook.
    - question: The query/prompt containing engineering questions or code requests.
    """
    try:
        client = await _get_authenticated_client()
        
        # Query the notebook
        answer, _ = await client.query(notebook_id, question)
        
        await client.close()
        
        return {
            "status": "success",
            "answer": answer
        }
    except Exception as e:
        logger.error(f"Error in deep_query: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@mcp.tool()
async def authenticate(method: str = "browser") -> Dict[str, Any]:
    """
    Triggers Google Chrome to open and allows the user to log in manually.
    Once login is complete, automatically extracts the session cookies and writes them to the local '.env' file.

    Parameters:
    - method: Authentication method (currently only 'browser' is supported).
    """
    if method != "browser":
        return {
            "status": "error",
            "message": "Only 'browser' method is supported."
        }
    try:
        from src.browser_auth import run_browser_login
        await run_browser_login()
        return {
            "status": "success",
            "message": "Cookies extracted and saved successfully to .env."
        }
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    # Default behavior: run stdio transport for MCP integration
    mcp.run(transport="stdio")
