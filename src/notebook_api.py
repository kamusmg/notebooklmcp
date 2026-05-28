import json
import logging
import os
import time
import urllib.parse
import uuid
from pathlib import Path
from typing import Optional, Tuple, List, Any
import httpx
from src.google_auth import create_http_client
from src.exceptions import RpcStructureError, CaptchaRequiredError
from src.rpc_ids import RpcId
from src.status_codes import parse_research_status, parse_artifact_status

logger = logging.getLogger(__name__)


def safe_get(lst: Any, idx: int, default: Any = None, context: str = "") -> Any:
    """Defensive list access — logs warning instead of raising on invalid index."""
    if not isinstance(lst, list):
        logger.warning("safe_get(%s): expected list, got %s", context, type(lst).__name__)
        return default
    if len(lst) <= idx:
        logger.warning("safe_get(%s): idx %d >= len %d", context, idx, len(lst))
        return default
    return lst[idx]


class NotebookLMClient:
    def __init__(self, cookies_header: str, csrf_token: str, build_label: str):
        self.client = create_http_client(cookies_header)
        self.csrf_token = csrf_token
        self.build_label = build_label

    def _get_next_req_id(self) -> int:
        # UUID4 eliminates the race condition from the old shared counter
        return uuid.uuid4().int & 0x7FFFFFFF

    def _build_batch_url(self, rpc_id: str, path: str = "/") -> str:
        req_id = self._get_next_req_id()
        params = {
            "rpcids": rpc_id,
            "source-path": path,
            "bl": self.build_label,
            "hl": "en",
            "_reqid": str(req_id),
            "rt": "c",
        }
        query_string = urllib.parse.urlencode(params)
        return f"https://notebooklm.google.com/_/LabsTailwindUi/data/batchexecute?{query_string}"

    def _build_batch_body(self, rpc_id: str, params: list) -> str:
        params_json = json.dumps(params, separators=(",", ":"))
        f_req = [[[rpc_id, params_json, None, "generic"]]]
        f_req_json = json.dumps(f_req, separators=(",", ":"))
        body = f"f.req={urllib.parse.quote(f_req_json)}"
        if self.csrf_token:
            body += f"&at={urllib.parse.quote(self.csrf_token)}"
        return body + "&"

    def _build_query_body(self, params: list) -> str:
        params_json = json.dumps(params, separators=(",", ":"))
        f_req = [None, params_json]
        f_req_json = json.dumps(f_req, separators=(",", ":"))
        body = f"f.req={urllib.parse.quote(f_req_json)}"
        if self.csrf_token:
            body += f"&at={urllib.parse.quote(self.csrf_token)}"
        return body + "&"

    def _parse_batch_response(self, response_text: str) -> Optional[list]:
        if "Please verify you're human" in response_text or "captcha" in response_text.lower()[:1000]:
            raise CaptchaRequiredError(
                "Google requires CAPTCHA. Run authenticate() to complete manual login."
            )
        if response_text.startswith(")]}'"):
            response_text = response_text[4:]
        lines = response_text.strip().split("\n")
        for line in lines:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, list) and len(item) > 2 and item[0] == "wrb.fr":
                            return json.loads(item[2])
            except Exception:
                continue
        return None

    @staticmethod
    def _save_fixture(rpc_id: str, response_text: str) -> None:
        if os.getenv("RTK_CAPTURE_FIXTURES") != "1":
            return
        fixtures_dir = Path("tests/fixtures/responses")
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        dest = fixtures_dir / f"{rpc_id}_{ts}.txt"
        dest.write_text(response_text, encoding="utf-8")
        logger.info(f"[fixture] saved {dest}")

    async def create_notebook(self, title: str) -> str:
        """Creates a new notebook and returns its UUID.

        Args:
            title: Display name for the notebook.

        Returns:
            UUID string of the created notebook (e.g. "2ac5476a-...").

        Raises:
            RuntimeError: HTTP request to Google failed.
            RpcStructureError: Response structure was unexpected (Google API change?).
            CaptchaRequiredError: Google requires CAPTCHA. Run authenticate().
        """
        rpc_id = RpcId.CREATE_NOTEBOOK
        params = [title, None, None, [2], [1, None, None, None, None, None, None, None, None, None, [1]]]
        url = self._build_batch_url(rpc_id)
        body = self._build_batch_body(rpc_id, params)

        logger.info(f"Creating notebook: '{title}'")
        response = await self.client.post(url, content=body)
        self._save_fixture(rpc_id, response.text)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to create notebook. HTTP {response.status_code}")

        res = self._parse_batch_response(response.text)
        notebook_id = safe_get(res, 2, context="create_notebook.id") if res else None
        if notebook_id and isinstance(notebook_id, str):
            logger.info(f"Notebook created successfully with ID: {notebook_id}")
            return notebook_id

        raise RpcStructureError(f"Unexpected response structure when creating notebook: {response.text[:500]}")

    async def add_source_url(self, notebook_id: str, source_url: str) -> str:
        """Add a web URL or GitHub repository as a source in a notebook.

        Args:
            notebook_id: UUID of the target notebook.
            source_url: URL to add (http/https/git@). YouTube URLs are handled
                with a different payload structure automatically.

        Returns:
            source_id string assigned by Google (or "unknown_source_id" if
            the response structure was unexpected — source may still have been added).

        Raises:
            RuntimeError: HTTP request failed.
        """
        rpc_id = RpcId.ADD_SOURCE
        # Check if youtube url or general web
        is_youtube = "youtube.com" in source_url.lower() or "youtu.be" in source_url.lower()
        if is_youtube:
            source_data = [None, None, None, None, None, None, None, [source_url], None, None, 1]
        else:
            source_data = [None, None, [source_url], None, None, None, None, None, None, None, 1]

        params = [[source_data], notebook_id, [2], [1, None, None, None, None, None, None, None, None, None, [1]]]
        url = self._build_batch_url(rpc_id, path=f"/notebook/{notebook_id}")
        body = self._build_batch_body(rpc_id, params)

        logger.info(f"Adding source URL '{source_url}' to notebook {notebook_id}")
        response = await self.client.post(url, content=body)
        self._save_fixture(rpc_id, response.text)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to add source. HTTP {response.status_code}")

        res = self._parse_batch_response(response.text)
        if res and isinstance(res, list) and len(res) > 0:
            # Handle nested list structure in response
            if isinstance(res[0], list) and len(res[0]) > 0 and isinstance(res[0][0], list):
                source_info = res[0][0]
                source_id = source_info[0][0] if isinstance(source_info[0], list) else source_info[0]
                logger.info(f"Source added successfully with ID: {source_id}")
                return source_id

        logger.warning(f"Unexpected response structure when adding source: {response.text[:500]}")
        return "unknown_source_id"

    async def query(self, notebook_id: str, question: str, conversation_id: Optional[str] = None) -> Tuple[str, str]:
        """Ask a question to the notebook and return the answer + conversation ID.

        Args:
            notebook_id: UUID of the target notebook.
            question: Free-form question (min 3 chars).
            conversation_id: Reuse a previous session ID to maintain context. None = new session.

        Returns:
            Tuple (answer_text, conversation_id). Pass the second value back on follow-up
            questions to preserve conversational context.

        Raises:
            RuntimeError: HTTP request failed.
            CaptchaRequiredError: Google requires CAPTCHA.
        """
        req_id = self._get_next_req_id()
        url_params = {
            "bl": self.build_label,
            "hl": "en",
            "_reqid": str(req_id),
            "rt": "c"
        }
        query_string = urllib.parse.urlencode(url_params)
        query_url = f"https://notebooklm.google.com/_/LabsTailwindUi/data/google.internal.labs.tailwind.orchestration.v1.LabsTailwindOrchestrationService/GenerateFreeFormStreamed?{query_string}"

        conv_id = conversation_id or "session-" + urllib.parse.quote(os.urandom(6).hex())
        # params: [sources_array, question, conversation_history, [2, None, [1], [1]], conversation_id, null, null, notebook_id, 1]
        params = [[], question, None, [2, None, [1], [1]], conv_id, None, None, notebook_id, 1]
        body = self._build_query_body(params)

        logger.info(f"Sending query to notebook {notebook_id}: '{question}'")
        response = await self.client.post(query_url, content=body)
        self._save_fixture("GenerateFreeFormStreamed", response.text)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to query notebook. HTTP {response.status_code}")

        response_text = response.text
        if response_text.startswith(")]}'"):
            response_text = response_text[4:]

        lines = response_text.strip().split("\n")
        best_marked_answer = ""
        best_unmarked_answer = ""
        server_conv_id = conv_id

        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.isdigit():
                continue

            try:
                data = json.loads(line_str)
            except Exception:
                continue

            if not isinstance(data, list):
                continue

            for item in data:
                if isinstance(item, list) and len(item) > 2 and item[0] == "wrb.fr":
                    inner_json = item[2]
                    if not isinstance(inner_json, str):
                        continue
                    try:
                        inner_data = json.loads(inner_json)
                    except Exception:
                        continue

                    if isinstance(inner_data, list) and len(inner_data) > 0:
                        first = inner_data[0]
                        if isinstance(first, list) and len(first) > 0:
                            text = first[0]
                            if isinstance(text, str) and text:
                                is_answer = (
                                    len(first) > 4
                                    and isinstance(first[4], list)
                                    and len(first[4]) > 0
                                    and first[4][-1] == 1
                                )
                                if (
                                    len(first) > 2
                                    and isinstance(first[2], list)
                                    and first[2]
                                    and isinstance(first[2][0], str)
                                ):
                                    server_conv_id = first[2][0]

                                if is_answer and len(text) > len(best_marked_answer):
                                    best_marked_answer = text
                                elif not is_answer and len(text) > len(best_unmarked_answer):
                                    best_unmarked_answer = text

        answer = best_marked_answer if best_marked_answer else best_unmarked_answer
        if not answer:
            logger.warning("No answer text could be parsed from Google's response stream.")
            return "No answer received from Google NotebookLM.", server_conv_id

        return answer, server_conv_id

    async def start_research(self, notebook_id: str, query: str, mode: str = "deep") -> dict:
        """Start a web research session and return the task ID.

        Args:
            notebook_id: UUID of the target notebook.
            query: Research topic or question.
            mode: "fast" (quick results) or "deep" (comprehensive, takes longer).

        Returns:
            Dict with keys: task_id (str), report_id (str|None), status ("in_progress").

        Raises:
            ValueError: mode is not "fast" or "deep".
            RpcStructureError: Unexpected response from Google.
        """
        mode_lower = mode.lower()
        if mode_lower not in ("fast", "deep"):
            raise ValueError("mode must be either 'fast' or 'deep'")
        
        # 1 = Web, 2 = Drive (we use Web)
        source_type = 1
        
        if mode_lower == "fast":
            rpc_id = RpcId.START_FAST_RESEARCH
            params = [[query, source_type], None, 1, notebook_id]
        else:
            rpc_id = RpcId.START_DEEP_RESEARCH
            params = [None, [1], [query, source_type], 5, notebook_id]
            
        url = self._build_batch_url(rpc_id, path=f"/notebook/{notebook_id}")
        body = self._build_batch_body(rpc_id, params)
        
        logger.info(f"Starting {mode_lower} research on notebook {notebook_id} with query: '{query}'")
        response = await self.client.post(url, content=body)
        self._save_fixture(rpc_id, response.text)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to start research. HTTP {response.status_code}")
            
        res = self._parse_batch_response(response.text)
        if res and isinstance(res, list) and len(res) > 0:
            # For Deep Research (QA9ei), Google returns a list like [plan_id, task_id]
            # where task_id is the primary key used in the research list (e3bVqc)
            task_id = res[1] if (mode_lower == "deep" and len(res) > 1) else res[0]
            report_id = res[1] if len(res) > 1 else None
            return {
                "task_id": task_id,
                "report_id": report_id,
                "status": "in_progress"
            }
            
        raise RpcStructureError(f"Unexpected response when starting research: {response.text[:500]}")

    async def poll_research(self, notebook_id: str, task_id: str) -> dict:
        """Poll the status of a running research task.

        Args:
            notebook_id: UUID of the notebook containing the research.
            task_id: Task ID returned by start_research().

        Returns:
            Dict with keys: task_id, status ("in_progress"|"completed"|"failed"|"not_found"),
            query (str), sources (list of {url, title, report_markdown?}), report (str).
        """
        rpc_id = RpcId.POLL_RESEARCH
        params = [None, None, notebook_id]
        url = self._build_batch_url(rpc_id, path=f"/notebook/{notebook_id}")
        body = self._build_batch_body(rpc_id, params)
        
        response = await self.client.post(url, content=body)
        self._save_fixture(rpc_id, response.text)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to poll research. HTTP {response.status_code}")
            
        res = self._parse_batch_response(response.text)
        if not res or not isinstance(res, list) or len(res) == 0:
            return {"status": "no_research", "sources": []}
            
        # Unwrap nested lists if Google returns [[[task_data, ...]]]
        if isinstance(res[0], list) and len(res[0]) > 0 and isinstance(res[0][0], list):
            res = res[0]
            
        for task_data in res:
            if not isinstance(task_data, list) or len(task_data) == 0:
                continue
                
            curr_task_id = task_data[0]
            if curr_task_id != task_id:
                continue
                
            task_info = task_data[1] if len(task_data) > 1 else None
            if not task_info or not isinstance(task_info, list):
                continue
                
            query_inner = safe_get(task_info, 1, context="poll_research.query_inner")
            query_text = safe_get(query_inner, 0, default="", context="poll_research.query_text") if isinstance(query_inner, list) else ""
            status_code = safe_get(task_info, 4, context="poll_research.status_code")

            status = parse_research_status(status_code)

            sources_bundle = safe_get(task_info, 3, context="poll_research.sources_bundle")
            sources_data = safe_get(sources_bundle, 0, default=[], context="poll_research.sources_data") if isinstance(sources_bundle, list) else []
            
            parsed_sources = []
            report = ""
            
            for src in sources_data:
                if not isinstance(src, list) or len(src) < 2:
                    continue
                title = ""
                url_str = ""
                source_report = ""
                
                # Check if it is a report/text block (src[0] is None)
                if src[0] is None and len(src) > 1:
                    if isinstance(src[1], list) and len(src[1]) >= 2:
                        title = src[1][0]
                        source_report = src[1][1]
                    elif isinstance(src[1], str):
                        title = src[1]
                        # Report markdown is usually in src[6][0] or src[6]
                        src6 = safe_get(src, 6, context="poll_research.src6")
                        if isinstance(src6, list):
                            source_report = safe_get(src6, 0, default="", context="poll_research.src6[0]")
                        elif isinstance(src6, str):
                            source_report = src6
                else:
                    url_str = src[0] if isinstance(src[0], str) else ""
                    title = src[1] if len(src) > 1 and isinstance(src[1], str) else ""
                    
                if title or url_str:
                    s = {
                        "url": url_str,
                        "title": title,
                        "research_task_id": curr_task_id
                    }
                    if source_report:
                        s["report_markdown"] = source_report
                        report = source_report
                    parsed_sources.append(s)
            
            return {
                "task_id": curr_task_id,
                "status": status,
                "query": query_text,
                "sources": parsed_sources,
                "report": report
            }
            
        return {"status": "not_found", "sources": []}

    async def import_research_sources(self, notebook_id: str, task_id: str, sources: list) -> list:
        """Import a list of research sources into a notebook as permanent sources.

        Args:
            notebook_id: UUID of the target notebook.
            task_id: Research task ID returned by start_research / poll_research.
            sources: List of source dicts. Each dict should have:
                - url (str): Web URL for web-type sources.
                - title (str): Display title.
                - report_markdown (str, optional): Markdown content for report-type sources.

        Returns:
            List of imported source dicts with keys: id (str), title (str).
            Empty list if nothing was imported.

        Raises:
            RuntimeError: HTTP request failed.

        Note:
            This operation is NOT idempotent — calling twice may create duplicate sources.
            Do not apply retry logic to this method.
        """
        rpc_id = RpcId.IMPORT_RESEARCH_SOURCES
        source_array = []
        
        for src in sources:
            if src.get("report_markdown"):
                # Report entry: type 3
                source_array.append([None, [src["title"], src["report_markdown"]], None, 3, None, None, None, None, None, None, 3])
            elif src.get("url"):
                # Web entry: type 2
                source_array.append([None, None, [src["url"], src.get("title", "Untitled")], None, None, None, None, None, None, None, 2])
                
        if not source_array:
            return []
            
        params = [None, [1], task_id, notebook_id, source_array]
        url = self._build_batch_url(rpc_id, path=f"/notebook/{notebook_id}")
        body = self._build_batch_body(rpc_id, params)
        
        logger.info(f"Importing {len(source_array)} sources for task {task_id} in notebook {notebook_id}")
        response = await self.client.post(url, content=body)
        self._save_fixture(rpc_id, response.text)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to import sources. HTTP {response.status_code}")
            
        res = self._parse_batch_response(response.text)
        imported = []
        if res and isinstance(res, list):
            if len(res) > 0 and isinstance(res[0], list) and len(res[0]) > 0 and isinstance(res[0][0], list):
                res = res[0]
            for src_data in res:
                if isinstance(src_data, list) and len(src_data) >= 2:
                    src_id = src_data[0][0] if src_data[0] and isinstance(src_data[0], list) else None
                    if src_id:
                        imported.append({"id": src_id, "title": src_data[1]})
        return imported

    async def get_source_ids(self, notebook_id: str) -> list:
        """Get the list of source IDs currently linked to a notebook.

        Args:
            notebook_id: UUID of the target notebook.

        Returns:
            List of source ID strings. Empty list if the notebook has no sources
            or the response structure was unexpected.

        Raises:
            RuntimeError: HTTP request failed.
        """
        rpc_id = RpcId.GET_NOTEBOOK
        params = [notebook_id, None, [2], None, 0]
        url = self._build_batch_url(rpc_id, path=f"/notebook/{notebook_id}")
        body = self._build_batch_body(rpc_id, params)
        
        response = await self.client.post(url, content=body)
        self._save_fixture(rpc_id, response.text)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to get notebook. HTTP {response.status_code}")
            
        res = self._parse_batch_response(response.text)
        source_ids = []
        nb_info = safe_get(res, 0, context="get_source_ids.nb_info") if res else None
        if isinstance(nb_info, list):
            sources = safe_get(nb_info, 1, context="get_source_ids.sources")
            if isinstance(sources, list):
                for src in sources:
                    if isinstance(src, list) and src:
                        first = safe_get(src, 0, context="get_source_ids.src[0]")
                        if isinstance(first, list) and first:
                            sid = safe_get(first, 0, context="get_source_ids.sid")
                            if isinstance(sid, str):
                                source_ids.append(sid)
        return source_ids

    async def generate_studio_artifact(self, notebook_id: str, source_ids: list, artifact_type: str, custom_prompt: str = None) -> str:
        """Trigger generation of a Studio artifact and return its artifact ID.

        Args:
            notebook_id: UUID of the target notebook.
            source_ids: List of source ID strings to include (from get_source_ids).
            artifact_type: One of: study_guide, briefing_doc, blog_post, quiz,
                slide_deck, data_table, custom.
            custom_prompt: Optional extra instructions appended to the default prompt
                (for study_guide/briefing_doc/blog_post) or used as the full prompt
                (for quiz/slide_deck/data_table/custom).

        Returns:
            artifact_id string to pass to poll_studio_artifact.

        Raises:
            RuntimeError: HTTP request failed.
            RpcStructureError: Google's response did not contain a usable artifact ID.
        """
        rpc_id = RpcId.CREATE_ARTIFACT
        
        # Nest source IDs: double = [[id, ...]], triple = [[[id, ...]]]
        source_ids_double = [source_ids]
        source_ids_triple = [[source_ids]]
        
        type_lower = artifact_type.lower()
        
        if type_lower == "study_guide":
            type_code = 2
            config = [
                None,
                [
                    "Study Guide",
                    "Short-answer quiz, essay questions, glossary",
                    None,
                    source_ids_double,
                    "en",
                    "Create a comprehensive study guide that includes key concepts, short-answer practice questions, essay prompts for deeper exploration, and a glossary of important terms." + (f"\n\nExtra instructions:\n{custom_prompt}" if custom_prompt else ""),
                    None,
                    True
                ]
            ]
            params = [[2], notebook_id, [None, None, type_code, source_ids_triple, None, None, None, config]]
            
        elif type_lower == "briefing_doc":
            type_code = 2
            config = [
                None,
                [
                    "Briefing Doc",
                    "Key insights and important quotes",
                    None,
                    source_ids_double,
                    "en",
                    "Create a comprehensive briefing document that includes an Executive Summary, detailed analysis of key themes, important quotes with context, and actionable insights." + (f"\n\nExtra instructions:\n{custom_prompt}" if custom_prompt else ""),
                    None,
                    True
                ]
            ]
            params = [[2], notebook_id, [None, None, type_code, source_ids_triple, None, None, None, config]]
            
        elif type_lower == "blog_post":
            type_code = 2
            config = [
                None,
                [
                    "Blog Post",
                    "Insightful takeaways in readable article format",
                    None,
                    source_ids_double,
                    "en",
                    "Write an engaging blog post that presents the key insights in an accessible, reader-friendly format. Include an attention-grabbing introduction, well-organized sections, and a compelling conclusion with takeaways." + (f"\n\nExtra instructions:\n{custom_prompt}" if custom_prompt else ""),
                    None,
                    True
                ]
            ]
            params = [[2], notebook_id, [None, None, type_code, source_ids_triple, None, None, None, config]]
            
        elif type_lower == "quiz":
            type_code = 4 # QUIZ_FLASHCARD
            quiz_config = [
                None,
                [
                    2, # variant = 2 (Quiz)
                    None,
                    custom_prompt or "",
                    None,
                    None,
                    None,
                    None,
                    [2, 2] # quantity, difficulty
                ]
            ]
            params = [[2], notebook_id, [None, None, type_code, source_ids_triple, None, None, None, None, None, quiz_config]]
            
        elif type_lower == "slide_deck":
            type_code = 8
            slide_config = [[custom_prompt or "", "en", 1, 1]]
            artifact_block = [None, None, type_code, source_ids_triple] + [None]*12 + [slide_config]
            params = [[2], notebook_id, artifact_block]
            
        elif type_lower == "data_table":
            type_code = 9
            table_config = [None, [custom_prompt or "", "en"]]
            artifact_block = [None, None, type_code, source_ids_triple] + [None]*14 + [table_config]
            params = [[2], notebook_id, artifact_block]
            
        else: # custom
            type_code = 2
            config = [
                None,
                [
                    "Custom Report",
                    "Custom format",
                    None,
                    source_ids_double,
                    "en",
                    custom_prompt or "Create a report based on the provided sources.",
                    None,
                    True
                ]
            ]
            params = [[2], notebook_id, [None, None, type_code, source_ids_triple, None, None, None, config]]
            
        url = self._build_batch_url(rpc_id, path=f"/notebook/{notebook_id}")
        body = self._build_batch_body(rpc_id, params)
        
        logger.info(f"Generating studio artifact '{type_lower}' for notebook {notebook_id}")
        response = await self.client.post(url, content=body)
        self._save_fixture(rpc_id, response.text)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to generate artifact. HTTP {response.status_code}")
            
        res = self._parse_batch_response(response.text)
        if res and isinstance(res, list) and len(res) > 0:
            inner = res[0]
            if isinstance(inner, list) and len(inner) > 0:
                artifact_id = inner[0]
                return str(artifact_id)
                
        raise RpcStructureError(f"Unexpected response during artifact generation: {response.text[:500]}")

    async def poll_studio_artifact(self, notebook_id: str, artifact_id: str) -> dict:
        """Poll the status and retrieve the content of a Studio artifact.

        Args:
            notebook_id: UUID of the notebook that owns the artifact.
            artifact_id: Artifact ID returned by generate_studio_artifact.

        Returns:
            Dict with keys:
                - artifact_id (str): Same as input.
                - title (str): Artifact display name.
                - type_code (int): Internal type code (2=report, 4=quiz, 8=slides, 9=table).
                - status (str): "in_progress", "completed", or "failed".
                - content (str): Markdown content — only populated when status="completed"
                    and type_code=2 (text-based artifacts).
            Returns {"status": "not_found"} if the artifact ID isn't in the list.

        Raises:
            RuntimeError: HTTP request failed.
        """
        rpc_id = RpcId.LIST_ARTIFACTS
        params = [[2], notebook_id]
        url = self._build_batch_url(rpc_id, path=f"/notebook/{notebook_id}")
        body = self._build_batch_body(rpc_id, params)
        
        response = await self.client.post(url, content=body)
        self._save_fixture(rpc_id, response.text)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to list artifacts. HTTP {response.status_code}")
            
        res = self._parse_batch_response(response.text)
        if not res or not isinstance(res, list):
            return {"status": "not_found"}
            
        if len(res) == 1 and isinstance(res[0], list) and (not res[0] or isinstance(res[0][0], list)):
            res = res[0]
            
        for art in res:
            if not (isinstance(art, list) and art):
                continue
            if str(safe_get(art, 0, context="poll_artifact.id")) != artifact_id:
                continue

            status_code = safe_get(art, 4, default=0, context="poll_artifact.status_code")
            type_code = safe_get(art, 2, default=0, context="poll_artifact.type_code")
            title = safe_get(art, 1, default="", context="poll_artifact.title")

            status = parse_artifact_status(status_code)

            content = ""
            # For reports/markdown artifacts (type=2), completed content is at index 5
            if status == "completed" and type_code == 2:
                raw = safe_get(art, 5, context="poll_artifact.content")
                content = raw if isinstance(raw, str) else ""

            return {
                "artifact_id": artifact_id,
                "title": title,
                "type_code": type_code,
                "status": status,
                "content": content
            }
                
        return {"status": "not_found"}

    async def close(self):
        await self.client.aclose()
