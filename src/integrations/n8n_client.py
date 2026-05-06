"""n8n HTTP client for OMNIS workflow triggers.

Padrão de uso pelo OMNIS — chamadas HTTP locais para n8n :5678.
NÃO faz chamadas externas, apenas localhost ou host configurado via env.
"""
import os
from typing import Any, Optional

import httpx


class N8NClient:
    """Cliente fino para disparar workflows n8n via HTTP."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or os.getenv("N8N_URL", "http://localhost:5678")
        self.api_key = api_key or os.getenv("N8N_API_KEY", "")

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["X-N8N-API-KEY"] = self.api_key
        return h

    def trigger(
        self,
        workflow_id: str,
        payload: dict,
        timeout_s: int = 120,
    ) -> dict[str, Any]:
        """Dispara workflow n8n e retorna a resposta."""
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}/execute"
        with httpx.Client(timeout=timeout_s) as client:
            r = client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()

    def health_check(self) -> bool:
        """Confere se n8n está respondendo em :5678."""
        try:
            with httpx.Client(timeout=5) as client:
                r = client.get(f"{self.base_url}/healthz")
                return r.status_code == 200
        except Exception:
            return False
