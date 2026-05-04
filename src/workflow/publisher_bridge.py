"""Publisher Bridge — HTTP client para Publisher OS API.

Chama os endpoints do Publisher Core (`:8000`) e MCP server.
Usado pelo Workflow Engine para os estágios PRODUCE e QUEUE.
"""

import json
import logging
import os
from typing import Optional
from urllib.parse import urljoin

import httpx

logger = logging.getLogger(__name__)

PUBLISHER_API_URL = os.getenv("PUBLISHER_API_URL", "http://localhost:8000")
MCP_API_URL = os.getenv("PUBLISHER_MCP_URL", "http://localhost:8000")
TIMEOUT = float(os.getenv("PUBLISHER_TIMEOUT", "120"))


class PublisherBridgeError(Exception):
    pass


class PublisherBridge:
    """Cliente HTTP para o Publisher OS."""

    def __init__(self, api_url: str = PUBLISHER_API_URL,
                 mcp_url: str = MCP_API_URL):
        self.api_url = api_url.rstrip("/")
        self.mcp_url = mcp_url.rstrip("/")
        self._client = httpx.Client(timeout=TIMEOUT)

    # ── Health ────────────────────────────────────────────

    def health(self) -> dict:
        """Verifica saúde do Publisher OS."""
        try:
            resp = self._client.get(f"{self.api_url}/health", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            return {"status": "unreachable", "error": str(e)}

    # ── CrewAI ────────────────────────────────────────────

    def run_crew(self, topic: str, pagina: str, formato: str,
                 crew_type: str = "content_production") -> dict:
        """Dispara uma crew de produção no Publisher OS.

        POST /api/v1/crews/run
        """
        payload = {
            "crew_type": crew_type,
            "topic": topic,
            "page": pagina,
            "format_type": formato,
        }
        try:
            resp = self._client.post(
                f"{self.api_url}/api/v1/crews/run",
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            raise PublisherBridgeError(f"Falha ao chamar crew: {e}")
        except httpx.HTTPStatusError as e:
            raise PublisherBridgeError(
                f"Publisher OS retornou {e.response.status_code}: {e.response.text[:200]}"
            )

    def crew_status(self, job_id: str) -> dict:
        """Verifica status de uma crew.

        GET /api/v1/crews/{job_id}/status
        """
        try:
            resp = self._client.get(
                f"{self.api_url}/api/v1/crews/{job_id}/status",
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            return {"status": "unknown", "error": str(e)}

    # ── MCP Tools ─────────────────────────────────────────

    def _mcp_call(self, tool_name: str, params: dict) -> dict:
        """Chama uma tool do MCP server via HTTP.

        O MCP server expõe tools em /api/v1/mcp/{tool_name}
        ou via o endpoint unificado.
        """
        try:
            resp = self._client.post(
                f"{self.mcp_url}/api/v1/mcp/{tool_name}",
                json=params,
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            raise PublisherBridgeError(f"MCP tool '{tool_name}' falhou: {e}")
        except httpx.HTTPStatusError as e:
            raise PublisherBridgeError(
                f"MCP '{tool_name}' retornou {e.response.status_code}: {e.response.text[:200]}"
            )

    def produce_content(self, tema: str, pagina: str, formato: str) -> dict:
        """MCP: produce_content — cria job de produção."""
        return self._mcp_call("produce_content", {
            "tema": tema,
            "pagina": pagina,
            "formato": formato,
        })

    def check_job(self, job_id: str) -> dict:
        """MCP: check_job — verifica status do job."""
        return self._mcp_call("check_job", {"job_id": job_id})

    def evaluate_content(self, content: str, pagina: str, formato: str) -> dict:
        """MCP: evaluate_content — avalia qualidade."""
        return self._mcp_call("evaluate_content", {
            "content": content,
            "pagina": pagina,
            "formato": formato,
        })

    def argos_enqueue_post(self, post_id: str) -> dict:
        """MCP: argos_enqueue_post — enfileira post no BullMQ."""
        return self._mcp_call("argos_enqueue_post", {"post_id": post_id})

    def argos_schedule_post(self, post_id: str, scheduled_at: str) -> dict:
        """MCP: argos_schedule_post — agenda post."""
        return self._mcp_call("argos_schedule_post", {
            "post_id": post_id,
            "scheduled_at": scheduled_at,
        })

    def argos_list_queue(self, status: str = "") -> dict:
        """MCP: argos_list_queue — lista fila de publicação."""
        return self._mcp_call("argos_list_queue", {"status": status})

    # ── Briefing ──────────────────────────────────────────

    def get_briefing(self) -> dict:
        """MCP: get_briefing — briefing diário do CEO."""
        return self._mcp_call("get_briefing", {})

    def get_trends(self, nicho: str) -> dict:
        """MCP: get_trends — tendências do nicho."""
        return self._mcp_call("get_trends", {"nicho": nicho})

    # ── Cleanup ───────────────────────────────────────────

    def close(self):
        self._client.close()
