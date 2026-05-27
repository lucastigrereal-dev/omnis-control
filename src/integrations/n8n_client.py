"""N8NClient — dispara workflows n8n por código.

Padrão de uso pelo OMNIS — chamadas HTTP locais para n8n :5678.
NÃO faz chamadas externas, apenas localhost ou host configurado via env.
"""
from __future__ import annotations
import os
from typing import Any, Optional


class N8NClient:
    """Trigger client para workflows n8n.

    Graceful degradation: se n8n não estiver rodando, retorna
    {"status": "unavailable"} sem levantar exceção.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.base_url = base_url or os.getenv("N8N_BASE_URL", None) or os.getenv("N8N_URL", "http://localhost:5678")
        self.api_key = api_key or os.getenv("N8N_API_KEY", "")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["X-N8N-API-KEY"] = self.api_key
        return h

    # ------------------------------------------------------------------
    # Low-level API (workflow execute by ID)
    # ------------------------------------------------------------------

    def trigger(
        self,
        workflow_id: str,
        payload: dict,
        timeout_s: int = 120,
    ) -> dict[str, Any]:
        """Dispara workflow n8n pelo ID e retorna a resposta."""
        import httpx
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}/execute"
        with httpx.Client(timeout=timeout_s) as client:
            r = client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()

    # ------------------------------------------------------------------
    # Webhook-based trigger (graceful degradation)
    # ------------------------------------------------------------------

    def trigger_workflow(self, webhook_path: str, payload: dict) -> dict:
        """Dispara um workflow via webhook.

        Retorna {"status": "unavailable", "error": ...} se n8n estiver off.
        """
        try:
            import httpx
            response = httpx.post(
                f"{self.base_url}/webhook/{webhook_path}",
                json=payload,
                timeout=10,
            )
            return response.json()
        except Exception as e:
            return {"status": "unavailable", "error": str(e)}

    # ------------------------------------------------------------------
    # High-level domain triggers
    # ------------------------------------------------------------------

    def trigger_content_production(self, tema: str, pagina: str) -> dict:
        """Dispara produção de conteúdo para um tema e página."""
        return self.trigger_workflow("nova-ideia", {"ideia": tema, "paginas": [pagina]})

    def trigger_lead_processing(self, mensagem: str, origem: str) -> dict:
        """Envia novo lead para processamento no n8n."""
        return self.trigger_workflow("novo-lead", {"mensagem": mensagem, "origem": origem})

    def trigger_sprint_creation(self, ideias: list[dict]) -> dict:
        """Dispara criação de sprint com lista de ideias."""
        return self.trigger_workflow("criar-sprint", {"ideias": ideias})

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Retorna True se n8n estiver acessível."""
        try:
            import httpx
            r = httpx.get(f"{self.base_url}/healthz", timeout=3)
            return r.status_code == 200
        except Exception:
            return False
