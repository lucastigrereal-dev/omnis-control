"""NotionConnector — Cliente REST para o Notion via stdlib urllib.

Princípios:
- Sem dependências extras: usa urllib.request (stdlib Python)
- Lê NOTION_TOKEN de os.environ — nunca hardcoded
- Cada método tem try/except → retorna [] / None / {} graciosamente
- Timeout 8s por chamada (API externa)
- Suporta: search, get_page, get_database, query_database, create_page
- Integrado à Aurora via ContextEngine._fetch_notion()

Uso:
    from src.notion.connector import NotionConnector
    nc = NotionConnector()
    results = nc.search("hoteis natal")
    pages = nc.query_database("database-id-aqui")
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Optional

_logger = logging.getLogger("omnis.notion.connector")

_NOTION_API = "https://api.notion.com/v1"
_NOTION_VERSION = "2022-06-28"
_TIMEOUT_S = 8


@dataclass
class NotionPage:
    """Página ou database do Notion."""
    page_id: str
    title: str
    object_type: str   # "page" | "database"
    url: str
    created_time: str
    last_edited: str
    properties: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "page_id": self.page_id,
            "title": self.title,
            "object_type": self.object_type,
            "url": self.url,
            "created_time": self.created_time,
            "last_edited": self.last_edited,
            "properties": self.properties,
        }

    def summary(self) -> str:
        return f"[{self.object_type}] {self.title} ({self.url})"


@dataclass
class NotionBlock:
    """Bloco de conteúdo de uma página Notion."""
    block_id: str
    block_type: str    # paragraph | heading_1 | bulleted_list_item | etc.
    text: str

    def to_dict(self) -> dict:
        return {
            "block_id": self.block_id,
            "block_type": self.block_type,
            "text": self.text,
        }


class NotionConnector:
    """Cliente REST para o Notion via urllib stdlib.

    Lê NOTION_TOKEN de os.environ. Se ausente, todos os métodos retornam
    dados vazios com graceful degradation — nunca lança exceção.

    Uso:
        nc = NotionConnector()
        if nc.is_available():
            pages = nc.search("campanha hotel natal")
    """

    def __init__(self, token: Optional[str] = None) -> None:
        self._token = token or os.environ.get("NOTION_TOKEN", "")

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Retorna True se NOTION_TOKEN está configurado."""
        return bool(self._token)

    def whoami(self) -> dict:
        """Retorna info do bot (name, type). Retorna {} se falhar."""
        return self._get("users/me") or {}

    # ------------------------------------------------------------------
    # Busca
    # ------------------------------------------------------------------

    def search(
        self,
        query: str = "",
        page_size: int = 10,
        filter_type: Optional[str] = None,  # "page" | "database" | None
    ) -> list[NotionPage]:
        """Busca páginas/databases no Notion que o bot tem acesso.

        Retorna [] se nenhuma página foi compartilhada com o bot OMNIS ou se falhar.
        """
        if not self._token:
            return []

        payload: dict = {"page_size": min(max(1, page_size), 100)}
        if query:
            payload["query"] = query
        if filter_type in ("page", "database"):
            payload["filter"] = {"value": filter_type, "property": "object"}

        data = self._post("search", payload)
        if data is None:
            return []

        pages = []
        for item in data.get("results", []):
            page = self._parse_page(item)
            if page:
                pages.append(page)

        _logger.debug("notion.search: query=%r → %d resultados", query, len(pages))
        return pages

    # ------------------------------------------------------------------
    # Página
    # ------------------------------------------------------------------

    def get_page(self, page_id: str) -> Optional[NotionPage]:
        """Retorna metadados de uma página específica."""
        if not self._token or not page_id:
            return None
        data = self._get(f"pages/{page_id}")
        return self._parse_page(data) if data else None

    def get_page_blocks(self, page_id: str, page_size: int = 50) -> list[NotionBlock]:
        """Retorna os blocos de conteúdo de uma página."""
        if not self._token or not page_id:
            return []

        data = self._get(f"blocks/{page_id}/children?page_size={page_size}")
        if not data:
            return []

        blocks = []
        for item in data.get("results", []):
            block = self._parse_block(item)
            if block:
                blocks.append(block)

        _logger.debug("notion.get_page_blocks: %s → %d blocos", page_id[:8], len(blocks))
        return blocks

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------

    def query_database(
        self,
        database_id: str,
        filter_payload: Optional[dict] = None,
        page_size: int = 20,
    ) -> list[NotionPage]:
        """Consulta entradas de um database Notion.

        filter_payload: dict no formato Notion filter API (opcional).
        """
        if not self._token or not database_id:
            return []

        payload: dict = {"page_size": min(max(1, page_size), 100)}
        if filter_payload:
            payload["filter"] = filter_payload

        data = self._post(f"databases/{database_id}/query", payload)
        if data is None:
            return []

        pages = []
        for item in data.get("results", []):
            page = self._parse_page(item)
            if page:
                pages.append(page)

        _logger.debug(
            "notion.query_database: %s → %d entradas", database_id[:8], len(pages)
        )
        return pages

    def get_database(self, database_id: str) -> dict:
        """Retorna metadados do database (schema, título). Retorna {} se falhar."""
        if not self._token or not database_id:
            return {}
        return self._get(f"databases/{database_id}") or {}

    # ------------------------------------------------------------------
    # Criação
    # ------------------------------------------------------------------

    def create_page(
        self,
        parent_page_id: str,
        title: str,
        content_blocks: Optional[list[dict]] = None,
    ) -> Optional[str]:
        """Cria uma nova página como filha de parent_page_id.

        Retorna o ID da página criada, ou None se falhar.
        content_blocks: lista de blocos no formato Notion API (opcional).
        """
        if not self._token or not parent_page_id:
            return None

        payload: dict = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "properties": {
                "title": {
                    "title": [{"type": "text", "text": {"content": title}}]
                }
            },
        }
        if content_blocks:
            payload["children"] = content_blocks

        data = self._post("pages", payload)
        if data and "id" in data:
            page_id = data["id"]
            _logger.info("notion.create_page: criado '%s' id=%s", title, page_id[:8])
            return page_id

        return None

    # ------------------------------------------------------------------
    # HTTP helpers (urllib stdlib, sem dependências)
    # ------------------------------------------------------------------

    def _get(self, path: str) -> Optional[dict]:
        """GET para a API do Notion. Retorna dict ou None."""
        if not self._token:
            return None
        url = f"{_NOTION_API}/{path}"
        req = urllib.request.Request(
            url,
            headers=self._headers(),
            method="GET",
        )
        return self._call(req)

    def _post(self, path: str, payload: dict) -> Optional[dict]:
        """POST para a API do Notion. Retorna dict ou None."""
        if not self._token:
            return None
        url = f"{_NOTION_API}/{path}"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={**self._headers(), "Content-Type": "application/json"},
            method="POST",
        )
        return self._call(req)

    def _call(self, req: urllib.request.Request) -> Optional[dict]:
        """Executa a requisição HTTP e trata erros graciosamente."""
        try:
            with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            _logger.warning("notion: HTTP %d — %s (%s)", exc.code, exc.reason, req.full_url)
            return None
        except urllib.error.URLError as exc:
            _logger.warning("notion: URLError — %s (%s)", exc.reason, req.full_url)
            return None
        except Exception as exc:  # noqa: BLE001
            _logger.warning("notion: erro inesperado — %s: %s", type(exc).__name__, exc)
            return None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Notion-Version": _NOTION_VERSION,
        }

    # ------------------------------------------------------------------
    # Parsers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_page(item: dict) -> Optional[NotionPage]:
        """Converte resposta da API em NotionPage. None se inválido."""
        if not item or not isinstance(item, dict):
            return None

        obj_type = item.get("object", "")
        page_id = item.get("id", "")
        if not page_id:
            return None

        # Extrai título: pages têm props.title, databases têm top-level title
        title = ""
        props = item.get("properties", {})
        for prop in props.values():
            if isinstance(prop, dict) and prop.get("type") == "title":
                for part in prop.get("title", []):
                    title += part.get("plain_text", "")
                break

        if not title:
            for part in item.get("title", []):
                title += part.get("plain_text", "")

        if not title:
            title = f"[{obj_type} sem título]"

        return NotionPage(
            page_id=page_id,
            title=title,
            object_type=obj_type,
            url=item.get("url", ""),
            created_time=item.get("created_time", ""),
            last_edited=item.get("last_edited_time", ""),
            properties={k: v.get("type", "") for k, v in props.items()},
        )

    @staticmethod
    def _parse_block(item: dict) -> Optional[NotionBlock]:
        """Converte bloco da API em NotionBlock. None se inválido."""
        if not item or not isinstance(item, dict):
            return None

        block_id = item.get("id", "")
        block_type = item.get("type", "")
        if not block_id or not block_type:
            return None

        # Extrai texto do bloco (tipo pode ser paragraph, heading_1, bulleted_list_item, etc.)
        text = ""
        block_data = item.get(block_type, {})
        if isinstance(block_data, dict):
            rich_text = block_data.get("rich_text", [])
            for part in rich_text:
                if isinstance(part, dict):
                    text += part.get("plain_text", "")

        return NotionBlock(
            block_id=block_id,
            block_type=block_type,
            text=text,
        )
