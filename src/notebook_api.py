import json
import logging
import urllib.parse
from typing import Optional, Tuple
import httpx
from src.google_auth import create_http_client

logger = logging.getLogger(__name__)

class NotebookLMClient:
    def __init__(self, cookies_header: str, csrf_token: str, build_label: str):
        self.client = create_http_client(cookies_header)
        self.csrf_token = csrf_token
        self.build_label = build_label
        self.req_id_counter = 100000

    def _get_next_req_id(self) -> int:
        self.req_id_counter += 100000
        return self.req_id_counter

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

    async def create_notebook(self, title: str) -> str:
        """Creates a new notebook with the given title and returns its ID."""
        rpc_id = "CCqFvf"
        params = [title, None, None, [2], [1, None, None, None, None, None, None, None, None, None, [1]]]
        url = self._build_batch_url(rpc_id)
        body = self._build_batch_body(rpc_id, params)

        logger.info(f"Creating notebook: '{title}'")
        response = await self.client.post(url, content=body)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to create notebook. HTTP {response.status_code}")

        res = self._parse_batch_response(response.text)
        if res and isinstance(res, list) and len(res) > 2:
            notebook_id = res[2]
            logger.info(f"Notebook created successfully with ID: {notebook_id}")
            return notebook_id

        raise ValueError(f"Unexpected response structure when creating notebook: {response.text[:500]}")

    async def add_source_url(self, notebook_id: str, source_url: str) -> str:
        """Adds a web/git repository URL to the specified notebook."""
        rpc_id = "izAoDd"
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
        """Queries the notebook and returns the text response and a stream/session ID."""
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

    async def close(self):
        await self.client.aclose()
