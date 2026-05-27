"""Webhook receiver — n8n chama o OMNIS.

Recebe eventos do n8n e os processa de forma assíncrona.
Todas as rotas são write-accepting (POST) pois são notificações externas.
"""
from __future__ import annotations
import uuid

from fastapi import APIRouter, BackgroundTasks

router = APIRouter()


@router.post("/n8n/nova-ideia")
def webhook_nova_ideia(payload: dict, background_tasks: BackgroundTasks):
    """n8n envia nova ideia de conteúdo."""
    return {
        "status": "received",
        "task_id": f"ideia_{uuid.uuid4().hex[:8]}",
        "payload": payload,
        "note": "Marketing sector integration W16+",
    }


@router.post("/n8n/novo-lead")
def webhook_novo_lead(payload: dict):
    """n8n envia novo lead para qualificação."""
    return {
        "status": "received",
        "task_id": f"lead_{uuid.uuid4().hex[:8]}",
        "payload": payload,
    }


@router.post("/n8n/publicacao-ok")
def webhook_publicacao_ok(payload: dict):
    """n8n confirma publicação realizada."""
    return {"status": "received", "payload": payload}


@router.post("/n8n/metricas")
def webhook_metricas(payload: dict):
    """n8n envia métricas da semana."""
    return {"status": "received", "payload": payload}
