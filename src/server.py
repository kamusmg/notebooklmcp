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
from src.exceptions import AuthExpiredError, CaptchaRequiredError, NotebookLMError
from src.telemetry import tracker
from src.validators import validate_notebook_id, validate_url, validate_question, validate_mode, validate_artifact_type
from src.config import settings

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
async def deep_query(question: str, notebook_id: str = "") -> Dict[str, Any]:
    """
    Sends a query directly to the chat interface of the specified NotebookLM notebook,
    returning the grounded synthesized response. Consumes zero local token quota.

    Parameters:
    - question: The query/prompt containing engineering questions or code requests.
    - notebook_id: The ID of the NotebookLM notebook. If omitted, uses DEFAULT_NOTEBOOK_ID from .env.
    """
    try:
        if not notebook_id:
            notebook_id = settings.default_notebook_id
            if not notebook_id:
                raise ValueError("notebook_id is empty and DEFAULT_NOTEBOOK_ID is not set in .env")
        validate_notebook_id(notebook_id)
        validate_question(question)
        client = await _get_authenticated_client()

        # Query the notebook
        answer, _ = await client.query(notebook_id, question)
        tracker.track("deep_query")
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

@mcp.tool()
async def start_research(notebook_id: str, query: str, mode: str = "deep") -> Dict[str, Any]:
    """
    Starts an asynchronous web research session on the Google NotebookLM backend.
    
    Parameters:
    - notebook_id: The ID of the NotebookLM notebook.
    - query: The research query or topic to search on the web.
    - mode: The research depth ('fast' for quick results, 'deep' for detailed analysis).
    """
    try:
        validate_notebook_id(notebook_id)
        validate_question(query)
        validate_mode(mode)
        client = await _get_authenticated_client()
        result = await client.start_research(notebook_id, query, mode)
        tracker.track(f"start_research_{mode.lower()}")
        await client.close()
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Error in start_research: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@mcp.tool()
async def poll_research(notebook_id: str, task_id: str) -> Dict[str, Any]:
    """
    Checks the status of an active web research task in the notebook.
    
    Parameters:
    - notebook_id: The ID of the NotebookLM notebook.
    - task_id: The research task ID returned by start_research.
    """
    try:
        client = await _get_authenticated_client()
        result = await client.poll_research(notebook_id, task_id)
        await client.close()
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Error in poll_research: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@mcp.tool()
async def import_research_sources(notebook_id: str, task_id: str, sources: list) -> Dict[str, Any]:
    """
    Imports the discovered web search results or reports into the notebook as permanent sources.
    
    Parameters:
    - notebook_id: The ID of the NotebookLM notebook.
    - task_id: The research task ID.
    - sources: The list of source objects (containing 'url', 'title', and optionally 'report_markdown') to import.
    """
    try:
        client = await _get_authenticated_client()
        imported = await client.import_research_sources(notebook_id, task_id, sources)
        await client.close()
        return {
            "status": "success",
            "imported_sources": imported
        }
    except Exception as e:
        logger.error(f"Error in import_research_sources: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@mcp.tool()
async def get_notebook_sources(notebook_id: str) -> Dict[str, Any]:
    """
    Lists the IDs of all sources linked to a notebook.
    
    Parameters:
    - notebook_id: The ID of the NotebookLM notebook.
    """
    try:
        client = await _get_authenticated_client()
        source_ids = await client.get_source_ids(notebook_id)
        await client.close()
        return {
            "status": "success",
            "source_ids": source_ids
        }
    except Exception as e:
        logger.error(f"Error in get_notebook_sources: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@mcp.tool()
async def generate_studio_artifact(notebook_id: str, artifact_type: str, custom_prompt: str = None) -> Dict[str, Any]:
    """
    Generates a Studio artifact (Study Guide, Briefing Doc, FAQ/Quiz, etc.) based on all linked notebook sources.
    
    Parameters:
    - notebook_id: The ID of the NotebookLM notebook.
    - artifact_type: Type of artifact to create ('study_guide', 'briefing_doc', 'blog_post', 'quiz', 'slide_deck', 'data_table', or 'custom').
    - custom_prompt: Custom generation instructions or custom report template.
    """
    try:
        validate_notebook_id(notebook_id)
        validate_artifact_type(artifact_type)
        client = await _get_authenticated_client()

        # 1. Fetch active source IDs from the notebook
        source_ids = await client.get_source_ids(notebook_id)
        if not source_ids:
            await client.close()
            return {
                "status": "error",
                "message": "Cannot generate artifact: The notebook has no sources. Please add or research sources first."
            }
            
        # 2. Trigger the generation
        artifact_id = await client.generate_studio_artifact(notebook_id, source_ids, artifact_type, custom_prompt)
        await client.close()
        
        return {
            "status": "success",
            "artifact_id": artifact_id,
            "message": f"Artifact generation for '{artifact_type}' successfully initiated."
        }
    except Exception as e:
        logger.error(f"Error in generate_studio_artifact: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@mcp.tool()
async def poll_studio_artifact(notebook_id: str, artifact_id: str) -> Dict[str, Any]:
    """
    Polls the status of an active Studio artifact generation task.
    If the status is 'completed' and the artifact is a report/markdown, returns the contents.
    
    Parameters:
    - notebook_id: The ID of the NotebookLM notebook.
    - artifact_id: The artifact/task ID returned by generate_studio_artifact.
    """
    try:
        client = await _get_authenticated_client()
        result = await client.poll_studio_artifact(notebook_id, artifact_id)
        await client.close()
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Error in poll_studio_artifact: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """
    Verifies Google authentication status, cookie presence, and connectivity to NotebookLM.
    Use this tool first to diagnose auth issues before running other tools.
    """
    try:
        from src.google_auth import create_http_client
        cookies = get_google_cookies()
        if not cookies or len(cookies) < 2:
            return {
                "status": "error",
                "authenticated": False,
                "message": "Google cookies missing or incomplete. Run authenticate() to set them up."
            }
        cookie_header = format_cookie_header(cookies)
        async with create_http_client(cookie_header) as client:
            csrf_token, build_label = await refresh_at_and_bl(client)
            return {
                "status": "ok",
                "authenticated": True,
                "build_label": build_label,
                "cookies_present": list(cookies.keys()),
            }
    except AuthExpiredError:
        return {"status": "error", "authenticated": False, "message": "Google cookies expired. Run authenticate()."}
    except CaptchaRequiredError:
        return {"status": "error", "authenticated": False, "message": "Google requires CAPTCHA. Run authenticate()."}
    except Exception as e:
        return {"status": "error", "authenticated": False, "message": str(e)}


@mcp.tool()
async def usage_stats() -> Dict[str, Any]:
    """
    Returns local usage statistics (privacy-friendly, nothing sent externally).
    Data is stored in ~/.notebooklmcp/telemetry.json.
    """
    from src.telemetry import tracker
    return {"status": "success", "data": tracker.report()}


if __name__ == "__main__":
    # Default behavior: run stdio transport for MCP integration
    mcp.run(transport="stdio")
