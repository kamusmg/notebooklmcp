import asyncio
import logging
import sys
from dotenv import load_dotenv
from src.google_auth import get_google_cookies, format_cookie_header, refresh_at_and_bl
from src.google_auth import create_http_client
from src.notebook_api import NotebookLMClient

# Configure logging to see details
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("test-research-run")

load_dotenv()

async def run_test():
    # 1. Authenticate
    cookies = get_google_cookies()
    if not cookies:
        logger.error("Authentication cookies not found in .env!")
        return
        
    cookie_header = format_cookie_header(cookies)
    
    logger.info("Refreshing CSRF token and build label...")
    async with create_http_client(cookie_header) as temp_client:
        csrf_token, build_label = await refresh_at_and_bl(temp_client)
        
    client = NotebookLMClient(
        cookies_header=cookie_header,
        csrf_token=csrf_token,
        build_label=build_label
    )
    
    notebook_id = "2ac5476a-6ede-41f9-be43-f53c086cd64b"
    query = "Google NotebookLM API features Deep Research and Studio updates 2026"
    
    # 2. Start research
    logger.info("Step 1: Starting Deep Research on NotebookLM...")
    research_start = await client.start_research(notebook_id, query, mode="deep")
    task_id = research_start["task_id"]
    logger.info(f"Research started! Task ID: {task_id}")
    
    # 3. Poll research status
    logger.info("Step 2: Polling research status...")
    status = "in_progress"
    attempts = 0
    poll_result = None
    
    # Loop until we reach a terminal status (completed or failed)
    while status not in ("completed", "failed") and attempts < 60:
        attempts += 1
        await asyncio.sleep(5)
        poll_result = await client.poll_research(notebook_id, task_id)
        status = poll_result.get("status", "in_progress")
        sources_found = len(poll_result.get("sources", []))
        logger.info(f"Poll #{attempts}: Status = '{status}', Sources found so far = {sources_found}")
        
    if status != "completed":
        logger.error(f"Research failed or timed out. Status: {status}")
        await client.close()
        return
        
    logger.info("Step 3: Deep Research completed successfully!")
    logger.info(f"Report Summary:\n{poll_result.get('report')[:300]}...\n")
    
    # 4. Import sources
    logger.info("Step 4: Importing discovered web sources into the notebook...")
    sources_to_import = poll_result.get("sources", [])
    if sources_to_import:
        imported = await client.import_research_sources(notebook_id, task_id, sources_to_import)
        logger.info(f"Imported sources successfully: {imported}")
    else:
        logger.warning("No sources to import.")
        
    # 5. Query the notebook with the new context
    logger.info("Step 5: Querying the notebook about ways to improve this project using the researched context...")
    question = "Com base nas pesquisas recentes que importamos, quais são as melhores ideias ou atualizações planejadas para o Google NotebookLM que podemos integrar no nosso MCP?"
    answer, _ = await client.query(notebook_id, question)
    
    logger.info("=" * 60)
    logger.info(f"RESPONSE FROM NOTEBOOKLM:\n\n{answer}\n")
    logger.info("=" * 60)
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(run_test())
