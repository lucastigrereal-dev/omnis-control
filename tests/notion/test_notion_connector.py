"""Testes — NotionConnector (WAVE 6).

Cobre: is_available, search, get_page, get_page_blocks, query_database,
       create_page, graceful sem token, HTTP error handling, anti-teatro.
Todos os testes mockam urllib.request.urlopen (sem chamadas reais).
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from io import BytesIO
from unittest.mock import patch, MagicMock

import pytest

from src.notion.connector import NotionConnector, NotionPage, NotionBlock


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

class FakeResponse:
    """Simula urllib.request.urlopen response."""
    def __init__(self, data: dict, status: int = 200):
        self._body = json.dumps(data).encode("utf-8")
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def _mock_urlopen(data: dict):
    """Patch para urllib.request.urlopen retornando data."""
    return patch(
        "urllib.request.urlopen",
        return_value=FakeResponse(data),
    )


def _mock_http_error(code: int = 401):
    exc = urllib.error.HTTPError("url", code, "Unauthorized", {}, None)
    return patch("urllib.request.urlopen", side_effect=exc)


def _mock_url_error():
    exc = urllib.error.URLError("connection refused")
    return patch("urllib.request.urlopen", side_effect=exc)


def _make_page_item(title: str = "Minha Pagina", obj_type: str = "page") -> dict:
    return {
        "object": obj_type,
        "id": "aabbccdd-1122-3344-5566-778899aabbcc",
        "url": "https://notion.so/test",
        "created_time": "2026-01-01T00:00:00.000Z",
        "last_edited_time": "2026-05-01T00:00:00.000Z",
        "properties": {
            "title": {
                "type": "title",
                "title": [{"plain_text": title}],
            }
        },
    }


def _make_database_item(title: str = "Meu Database") -> dict:
    return {
        "object": "database",
        "id": "dddddddd-aaaa-bbbb-cccc-111111111111",
        "url": "https://notion.so/db",
        "created_time": "2026-01-01T00:00:00.000Z",
        "last_edited_time": "2026-05-01T00:00:00.000Z",
        "title": [{"plain_text": title}],
        "properties": {
            "Name": {"type": "title"},
            "Status": {"type": "select"},
        },
    }


def _make_block_item(text: str = "Texto do bloco", btype: str = "paragraph") -> dict:
    return {
        "object": "block",
        "id": "block-id-1234",
        "type": btype,
        btype: {
            "rich_text": [{"plain_text": text}]
        },
    }


# ------------------------------------------------------------------
# is_available
# ------------------------------------------------------------------

class TestIsAvailable:
    def test_sem_token_false(self):
        nc = NotionConnector(token="")
        assert nc.is_available() is False

    def test_com_token_true(self):
        nc = NotionConnector(token="abc123")
        assert nc.is_available() is True

    def test_sem_token_env_false(self, monkeypatch):
        monkeypatch.delenv("NOTION_TOKEN", raising=False)
        nc = NotionConnector()
        assert nc.is_available() is False


# ------------------------------------------------------------------
# whoami
# ------------------------------------------------------------------

class TestWhoami:
    def test_retorna_dict_com_nome(self):
        nc = NotionConnector(token="tok")
        with _mock_urlopen({"name": "OMNIS", "type": "bot", "id": "123"}):
            result = nc.whoami()
        assert result["name"] == "OMNIS"
        assert result["type"] == "bot"

    def test_http_error_retorna_vazio(self):
        nc = NotionConnector(token="tok")
        with _mock_http_error(401):
            result = nc.whoami()
        assert result == {}

    def test_sem_token_retorna_vazio(self):
        nc = NotionConnector(token="")
        result = nc.whoami()
        assert result == {}


# ------------------------------------------------------------------
# search
# ------------------------------------------------------------------

class TestSearch:
    def test_retorna_lista_de_pages(self):
        nc = NotionConnector(token="tok")
        payload = {"results": [_make_page_item("Campanha Hotel")], "has_more": False}
        with _mock_urlopen(payload):
            pages = nc.search("hotel")
        assert len(pages) == 1
        assert isinstance(pages[0], NotionPage)
        assert pages[0].title == "Campanha Hotel"

    def test_zero_resultados_retorna_lista_vazia(self):
        nc = NotionConnector(token="tok")
        with _mock_urlopen({"results": [], "has_more": False}):
            pages = nc.search("nada")
        assert pages == []

    def test_sem_token_retorna_vazio_sem_chamar_api(self):
        nc = NotionConnector(token="")
        pages = nc.search("qualquer")
        assert pages == []

    def test_http_error_retorna_vazio(self):
        nc = NotionConnector(token="tok")
        with _mock_http_error(403):
            pages = nc.search("campanha")
        assert pages == []

    def test_url_error_retorna_vazio(self):
        nc = NotionConnector(token="tok")
        with _mock_url_error():
            pages = nc.search("campanha")
        assert pages == []

    def test_page_e_database_parseados(self):
        nc = NotionConnector(token="tok")
        payload = {
            "results": [
                _make_page_item("Pagina Teste"),
                _make_database_item("DB Leads"),
            ],
            "has_more": False,
        }
        with _mock_urlopen(payload):
            pages = nc.search()
        assert len(pages) == 2
        types = {p.object_type for p in pages}
        assert "page" in types
        assert "database" in types

    def test_titulo_extraido_de_database(self):
        nc = NotionConnector(token="tok")
        payload = {"results": [_make_database_item("Leads Hoteis")], "has_more": False}
        with _mock_urlopen(payload):
            pages = nc.search()
        assert pages[0].title == "Leads Hoteis"

    def test_page_sem_titulo_usa_fallback(self):
        nc = NotionConnector(token="tok")
        item = _make_page_item()
        # Remove o título
        item["properties"]["title"]["title"] = []
        payload = {"results": [item], "has_more": False}
        with _mock_urlopen(payload):
            pages = nc.search()
        assert "sem título" in pages[0].title.lower() or "page" in pages[0].title.lower()

    def test_to_dict_estavel(self):
        nc = NotionConnector(token="tok")
        with _mock_urlopen({"results": [_make_page_item("Test")], "has_more": False}):
            pages = nc.search()
        d = pages[0].to_dict()
        assert "page_id" in d
        assert "title" in d
        assert "object_type" in d
        assert "url" in d


# ------------------------------------------------------------------
# get_page
# ------------------------------------------------------------------

class TestGetPage:
    def test_retorna_notion_page(self):
        nc = NotionConnector(token="tok")
        with _mock_urlopen(_make_page_item("Pagina Especifica")):
            page = nc.get_page("aabbccdd")
        assert page is not None
        assert page.title == "Pagina Especifica"

    def test_http_error_retorna_none(self):
        nc = NotionConnector(token="tok")
        with _mock_http_error(404):
            page = nc.get_page("inexistente")
        assert page is None

    def test_sem_token_retorna_none(self):
        nc = NotionConnector(token="")
        page = nc.get_page("qualquer")
        assert page is None


# ------------------------------------------------------------------
# get_page_blocks
# ------------------------------------------------------------------

class TestGetPageBlocks:
    def test_retorna_lista_de_blocks(self):
        nc = NotionConnector(token="tok")
        payload = {
            "results": [
                _make_block_item("Primeiro paragrafo"),
                _make_block_item("Segundo paragrafo"),
            ]
        }
        with _mock_urlopen(payload):
            blocks = nc.get_page_blocks("page-id")
        assert len(blocks) == 2
        assert isinstance(blocks[0], NotionBlock)
        assert blocks[0].text == "Primeiro paragrafo"

    def test_bloco_sem_texto_ainda_retornado(self):
        nc = NotionConnector(token="tok")
        item = _make_block_item("")
        payload = {"results": [item]}
        with _mock_urlopen(payload):
            blocks = nc.get_page_blocks("page-id")
        assert len(blocks) == 1
        assert blocks[0].text == ""

    def test_erro_retorna_vazio(self):
        nc = NotionConnector(token="tok")
        with _mock_http_error(403):
            blocks = nc.get_page_blocks("page-id")
        assert blocks == []

    def test_to_dict_bloco(self):
        nc = NotionConnector(token="tok")
        payload = {"results": [_make_block_item("Texto")]}
        with _mock_urlopen(payload):
            blocks = nc.get_page_blocks("page-id")
        d = blocks[0].to_dict()
        assert "block_id" in d
        assert "block_type" in d
        assert "text" in d


# ------------------------------------------------------------------
# query_database
# ------------------------------------------------------------------

class TestQueryDatabase:
    def test_retorna_entradas(self):
        nc = NotionConnector(token="tok")
        payload = {"results": [_make_page_item("Lead #1"), _make_page_item("Lead #2")]}
        with _mock_urlopen(payload):
            pages = nc.query_database("db-id")
        assert len(pages) == 2

    def test_sem_token_retorna_vazio(self):
        nc = NotionConnector(token="")
        pages = nc.query_database("db-id")
        assert pages == []

    def test_erro_retorna_vazio(self):
        nc = NotionConnector(token="tok")
        with _mock_url_error():
            pages = nc.query_database("db-id")
        assert pages == []


# ------------------------------------------------------------------
# create_page
# ------------------------------------------------------------------

class TestCreatePage:
    def test_retorna_id_da_pagina_criada(self):
        nc = NotionConnector(token="tok")
        response = {"id": "nova-pagina-id-aqui", "object": "page"}
        with _mock_urlopen(response):
            page_id = nc.create_page(
                parent_page_id="parent-id",
                title="Nova Pagina OMNIS",
            )
        assert page_id == "nova-pagina-id-aqui"

    def test_erro_retorna_none(self):
        nc = NotionConnector(token="tok")
        with _mock_http_error(400):
            page_id = nc.create_page("parent-id", "Titulo")
        assert page_id is None

    def test_sem_token_retorna_none(self):
        nc = NotionConnector(token="")
        page_id = nc.create_page("parent-id", "Titulo")
        assert page_id is None


# ------------------------------------------------------------------
# Anti-teatro
# ------------------------------------------------------------------

class TestAntiTeatro:
    def test_titulo_correto_refletido_na_page(self):
        """O título retornado deve ser exatamente o que veio da API."""
        TITULO = "ANTI_TEATRO_WAVE6_NOTION"
        nc = NotionConnector(token="tok")
        with _mock_urlopen({"results": [_make_page_item(TITULO)], "has_more": False}):
            pages = nc.search(TITULO)
        assert pages[0].title == TITULO

    def test_page_id_preservado(self):
        nc = NotionConnector(token="tok")
        item = _make_page_item()
        item["id"] = "custom-unique-id-w6"
        with _mock_urlopen({"results": [item], "has_more": False}):
            pages = nc.search()
        assert pages[0].page_id == "custom-unique-id-w6"

    def test_summary_contem_titulo_e_url(self):
        nc = NotionConnector(token="tok")
        with _mock_urlopen({"results": [_make_page_item("Hotel Ponta Negra")], "has_more": False}):
            pages = nc.search()
        s = pages[0].summary()
        assert "Hotel Ponta Negra" in s
        assert "https://notion.so" in s
