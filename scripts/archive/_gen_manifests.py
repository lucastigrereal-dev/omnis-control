#!/usr/bin/env python3
"""Generate manifest.json for all 17 executable skills."""
import json
import os
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(BASE, "skills")
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

skills = [
    {
        "name": "argos-bridge",
        "description": "Bridge entre Content Queue e ARGOS Drafts no Publisher OS",
        "risk_level": "medium", "mode": "external_action",
        "owner": "automation_integrations",
        "tags": ["argos", "bridge", "publisher-os", "draft"],
        "inputs": {"topic": "string", "pagina": "string", "formato": "string"},
        "inputs_req": ["topic"],
        "outputs": {"job_id": "string", "status": "string"},
        "outputs_req": ["job_id"],
        "approval": True, "lifecycle": "validated"
    },
    {
        "name": "create_30_day_content_calendar",
        "description": "Gera calendario editorial de 30 dias para um perfil Instagram",
        "risk_level": "low", "mode": "draft_only",
        "owner": "marketing_enterprise",
        "tags": ["calendar", "content", "planning", "instagram"],
        "inputs": {"perfil": "string", "mes": "string"},
        "inputs_req": ["perfil"],
        "outputs": {"calendar": "array", "slots": "integer"},
        "outputs_req": ["calendar"],
        "approval": False, "lifecycle": "production"
    },
    {
        "name": "create_instagram_carousel",
        "description": "Gera roteiro de carrossel para Instagram com brief de design",
        "risk_level": "low", "mode": "draft_only",
        "owner": "marketing_enterprise",
        "tags": ["carousel", "instagram", "content", "design"],
        "inputs": {"topic": "string", "perfil": "string", "slides": "integer"},
        "inputs_req": ["topic", "perfil"],
        "outputs": {"script": "array", "design_brief": "string"},
        "outputs_req": ["script"],
        "approval": False, "lifecycle": "production"
    },
    {
        "name": "create_sales_dm_sequence",
        "description": "Gera sequencia de DM para prospeccao B2B de hoteis",
        "risk_level": "low", "mode": "draft_only",
        "owner": "sales_revenue",
        "tags": ["sales", "dm", "b2b", "hotels", "prospecting"],
        "inputs": {"hotel": "string", "segment": "string"},
        "inputs_req": ["hotel"],
        "outputs": {"sequence": "array", "messages": "integer"},
        "outputs_req": ["sequence"],
        "approval": False, "lifecycle": "production"
    },
    {
        "name": "crm-pipeline",
        "description": "Pipeline de CRM local para vendas B2B com 6 modos",
        "risk_level": "medium", "mode": "local_write",
        "owner": "sales_revenue",
        "tags": ["crm", "sales", "pipeline", "b2b", "sqlite"],
        "inputs": {"mode": "string", "data": "object"},
        "inputs_req": ["mode"],
        "outputs": {"result": "string", "count": "integer"},
        "outputs_req": ["result"],
        "approval": False, "lifecycle": "production"
    },
    {
        "name": "export_content_batch_to_csv",
        "description": "Exporta lote da Content Queue para CSV",
        "risk_level": "low", "mode": "local_write",
        "owner": "marketing_enterprise",
        "tags": ["export", "csv", "content-queue", "batch"],
        "inputs": {"status": "string", "limit": "integer"},
        "inputs_req": [],
        "outputs": {"file": "string", "count": "integer"},
        "outputs_req": ["file"],
        "approval": False, "lifecycle": "production"
    },
    {
        "name": "generate_seogram_caption",
        "description": "Gera legenda SEO-otimizada para Instagram com palavras-chave",
        "risk_level": "low", "mode": "draft_only",
        "owner": "marketing_enterprise",
        "tags": ["caption", "seo", "instagram", "content"],
        "inputs": {"topic": "string", "perfil": "string", "keywords": "array"},
        "inputs_req": ["topic", "perfil"],
        "outputs": {"caption": "string", "seo_score": "number"},
        "outputs_req": ["caption"],
        "approval": False, "lifecycle": "production"
    },
    {
        "name": "jarvis-brain",
        "description": "Busca contexto multi-fonte (Akasha, Qdrant, Obsidian)",
        "risk_level": "low", "mode": "read_only",
        "owner": "memory_knowledge",
        "tags": ["brain", "context", "search", "memory", "core"],
        "inputs": {"query": "string", "sources": "array"},
        "inputs_req": ["query"],
        "outputs": {"context": "string", "sources_used": "array"},
        "outputs_req": ["context"],
        "approval": False, "lifecycle": "production"
    },
    {
        "name": "jarvis-decide",
        "description": "Decision Engine que prioriza acoes baseado em formula multi-fator",
        "risk_level": "low", "mode": "read_only",
        "owner": "mission_control",
        "tags": ["decide", "prioritization", "decision", "core"],
        "inputs": {"options": "array", "context": "string"},
        "inputs_req": ["options"],
        "outputs": {"ranking": "array", "selected": "string", "score": "number"},
        "outputs_req": ["ranking"],
        "approval": False, "lifecycle": "production"
    },
    {
        "name": "jarvis-delegate",
        "description": "Roteia requisicao para a skill mais adequada baseado no registry",
        "risk_level": "medium", "mode": "local_write",
        "owner": "mission_control",
        "tags": ["delegate", "router", "skills", "core"],
        "inputs": {"intent": "string", "params": "object"},
        "inputs_req": ["intent"],
        "outputs": {"skill": "string", "confidence": "number"},
        "outputs_req": ["skill"],
        "approval": False, "lifecycle": "production"
    },
    {
        "name": "jarvis-guardrails",
        "description": "Valida acoes contra regras de seguranca antes de executar",
        "risk_level": "low", "mode": "read_only",
        "owner": "security_audit",
        "tags": ["guardrails", "security", "validation", "core"],
        "inputs": {"action": "string", "params": "object"},
        "inputs_req": ["action"],
        "outputs": {"allowed": "boolean", "reason": "string", "severity": "string"},
        "outputs_req": ["allowed"],
        "approval": False, "lifecycle": "production"
    },
    {
        "name": "jarvis-memory-write",
        "description": "Persiste resultados de execucao em Akasha, Qdrant e git",
        "risk_level": "medium", "mode": "local_write",
        "owner": "memory_knowledge",
        "tags": ["memory", "persist", "akasha", "git", "core"],
        "inputs": {"content": "object", "source": "string", "tags": "array"},
        "inputs_req": ["content", "source"],
        "outputs": {"status": "string", "location": "string"},
        "outputs_req": ["status"],
        "approval": False, "lifecycle": "production"
    },
    {
        "name": "jarvis-morning",
        "description": "Briefing matinal com health score, acoes e metricas do ecossistema",
        "risk_level": "low", "mode": "read_only",
        "owner": "mission_control",
        "tags": ["morning", "briefing", "daily", "core"],
        "inputs": {},
        "inputs_req": [],
        "outputs": {"briefing": "string", "health_score": "number", "top_actions": "array"},
        "outputs_req": ["briefing"],
        "approval": False, "lifecycle": "production"
    },
    {
        "name": "jarvis-router",
        "description": "Classifica intencao do operador e roteia para o setor correto",
        "risk_level": "low", "mode": "read_only",
        "owner": "mission_control",
        "tags": ["router", "intent", "classification", "core"],
        "inputs": {"message": "string", "context": "string"},
        "inputs_req": ["message"],
        "outputs": {"sector": "string", "confidence": "number", "skill": "string"},
        "outputs_req": ["sector"],
        "approval": False, "lifecycle": "production"
    },
    {
        "name": "revenue-tracker",
        "description": "Rastreia receita de collabs e vendas com 4 modos (SQLite)",
        "risk_level": "medium", "mode": "local_write",
        "owner": "finance_capital",
        "tags": ["revenue", "finance", "tracker", "sqlite"],
        "inputs": {"mode": "string", "data": "object"},
        "inputs_req": ["mode"],
        "outputs": {"result": "string", "total": "number"},
        "outputs_req": ["result"],
        "approval": False, "lifecycle": "production"
    },
    {
        "name": "skill-creator",
        "description": "Cria novas skills no padrao OMNIS com SKILL.md, manifest.json e run.py",
        "risk_level": "high", "mode": "external_action",
        "owner": "produto_tecnologia",
        "tags": ["skill", "create", "scaffold", "core"],
        "inputs": {"name": "string", "description": "string", "mode": "string"},
        "inputs_req": ["name", "description"],
        "outputs": {"path": "string", "files": "array"},
        "outputs_req": ["path"],
        "approval": True, "lifecycle": "validated"
    },
    {
        "name": "video_to_content",
        "description": "Converte video bruto em formato publicavel com metadados",
        "risk_level": "medium", "mode": "local_write",
        "owner": "marketing_enterprise",
        "tags": ["video", "content", "conversion", "assets"],
        "inputs": {"video_path": "string", "perfil": "string"},
        "inputs_req": ["video_path"],
        "outputs": {"output_path": "string", "duration": "number", "status": "string"},
        "outputs_req": ["output_path"],
        "approval": False, "lifecycle": "validated"
    },
]

os.makedirs(SKILLS_DIR, exist_ok=True)
created = []
for s in skills:
    skill_dir = os.path.join(SKILLS_DIR, s["name"])
    os.makedirs(skill_dir, exist_ok=True)
    manifest = {
        "name": s["name"],
        "version": "1.0.0",
        "description": s["description"],
        "status": "active",
        "risk_level": s["risk_level"],
        "mode": s["mode"],
        "owner": s["owner"],
        "tags": s["tags"],
        "inputs_schema": {
            "type": "object",
            "properties": {k: {"type": v} for k, v in s["inputs"].items()},
            "required": s["inputs_req"]
        },
        "outputs_schema": {
            "type": "object",
            "properties": {k: {"type": v} for k, v in s["outputs"].items()},
            "required": s["outputs_req"]
        },
        "allowed_tools": [],
        "denied_tools": [],
        "dependencies": [],
        "permissions": {
            "allow_read_paths": [],
            "allow_write_paths": [],
            "allow_network": s["mode"] in ("external_action",)
        },
        "examples": [],
        "test_command": f"python -m src.cli skill-info {s['name']}",
        "approval_required": s["approval"],
        "lifecycle": s["lifecycle"],
        "deprecated": False,
        "replacement": "",
        "created_at": now,
        "updated_at": now
    }
    mf_path = os.path.join(skill_dir, "manifest.json")
    with open(mf_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    created.append(s["name"])

print(f"Created {len(created)} manifests in skills/:")
for c in created:
    print(f"  skills/{c}/manifest.json")
