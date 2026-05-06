#!/usr/bin/env python3
"""jarvis-delegate: Roteia intenção → setor → skill lendo registry canônico."""

import json
import os
import sys
from typing import Optional
import yaml

REGISTRY_DIR = os.path.expanduser("~/.claude/registry")
SECTORS_PATH = os.path.join(REGISTRY_DIR, "sectors.yaml")
SKILLS_PATH = os.path.join(REGISTRY_DIR, "skills.yaml")

# Mapa rápido intenção → skill (fallback se YAML não disponível)
INTENT_MAP = {
    "prospecta hotel": "sdr-hotel", "dm para hotel": "sdr-hotel", "prospectar": "sdr-hotel",
    "conteudo": "content-machine", "carrossel": "content-machine", "legenda": "content-machine",
    "reel": "content-machine", "gera conteudo": "content-machine",
    "pitch": "hotel-pitch-generator", "proposta hotel": "hotel-pitch-generator",
    "calendario editorial": "campaign-planner", "campanha": "campaign-planner",
    "roi": "instagram-roi-calculator", "quanto vale": "instagram-roi-calculator",
    "seo": "seogram-engine", "hashtags": "seogram-engine", "otimiza legenda": "seogram-engine",
    "busca": "postgresql-expert", "sql": "postgresql-expert", "banco": "postgresql-expert",
    "briefing": "jarvis-morning", "bom dia": "jarvis-morning", "missao do dia": "jarvis-morning",
    "status sistema": "jarvis-morning",
    "publisher-os": "publisher-os", "publisher": "publisher-os",
    "organizar": "mem-do", "organiza": "mem-do",
}


def carregar_registry() -> dict:
    """Carrega sectors.yaml e skills.yaml."""
    dados = {"sectors": [], "skills": {"jarvis_core": [], "custom": []}}
    try:
        if os.path.exists(SECTORS_PATH):
            with open(SECTORS_PATH) as f:
                dados["sectors"] = yaml.safe_load(f).get("sectors", [])
        if os.path.exists(SKILLS_PATH):
            skills_data = yaml.safe_load(open(SKILLS_PATH))
            dados["skills"]["jarvis_core"] = [s["id"] for s in skills_data.get("jarvis_core", [])
                                              if s.get("status") == "active"]
            dados["skills"]["custom"] = [s["id"] for s in skills_data.get("custom", [])
                                         if s.get("status") == "active"]
    except Exception:
        pass
    return dados


def classificar_setor(intencao: str, registry: dict) -> list:
    """Classifica setor por keywords."""
    intencao_lower = intencao.lower()

    # Tenta match direto no intent_map
    for pattern, skill in INTENT_MAP.items():
        if pattern in intencao_lower:
            # Encontra qual setor tem essa skill
            for sector in registry["sectors"]:
                if skill in [s.lower() for s in sector.get("skills", [])]:
                    return [sector["id"]]

    # Heurística por setor
    sector_keywords = {
        "midia_conteudo": ["conteudo", "post", "instagram", "publicar", "legenda", "reel"],
        "comercial_sdr": ["hotel", "vender", "publi", "collab", "dm", "prospectar", "parceria"],
        "vendas_crm": ["crm", "pipeline", "lead", "proposta", "fechar", "cliente"],
        "conhecimento_inteligencia": ["buscar", "saber", "conhecimento", "biblioteca", "livro"],
        "produto_tecnologia": ["app", "codigo", "docker", "deploy", "sistema", "tecnologia"],
        "financeiro_metricas": ["receita", "faturamento", "mrr", "roi", "custo", "dinheiro"],
        "operacoes_organizacao": ["organizar", "status", "rotina", "diagnostico", "tarefa"],
    }

    for sector_id, keywords in sector_keywords.items():
        if any(kw in intencao_lower for kw in keywords):
            return [sector_id]

    return ["operacoes_organizacao"]


def listar_candidatas(setor_ids: list[str], registry: dict) -> list:
    """Lista skills candidatas no setor."""
    candidatas = []
    for sector in registry["sectors"]:
        if sector["id"] in setor_ids:
            for skill_id in sector.get("skills", []):
                candidatas.append(skill_id)
            for skill_id in sector.get("skills_planned", []):
                candidatas.append(f"{skill_id} (planned)")
    return candidatas


def delegate(intencao: str, contexto: Optional[dict] = None) -> dict:
    """Pipeline principal de delegação."""
    registry = carregar_registry()
    setores = classificar_setor(intencao, registry)

    # Tenta match direto no intent_map
    intencao_lower = intencao.lower()
    skill_direta = None
    for pattern, skill in INTENT_MAP.items():
        if pattern in intencao_lower:
            skill_direta = skill
            break

    if skill_direta:
        resultado = {
            "intencao": intencao,
            "setor": setores[0] if setores else "operacoes_organizacao",
            "skill": skill_direta,
            "status": "delegado" if skill_direta else "gap",
            "skills_candidatas": [skill_direta],
            "contexto_coletado": bool(contexto),
            "metodo": "match_direto",
            "next_action": f"Executar {skill_direta} com contexto"
        }
        return resultado

    # Fallback: lista candidatas
    candidatas = listar_candidatas(setores, registry)

    if len(candidatas) == 1:
        resultado = {
            "intencao": intencao,
            "setor": setores[0],
            "skill": candidatas[0],
            "status": "delegado",
            "skills_candidatas": candidatas,
            "contexto_coletado": bool(contexto),
            "metodo": "unica_candidata",
            "next_action": f"Executar {candidatas[0]}"
        }
    elif len(candidatas) > 1:
        resultado = {
            "intencao": intencao,
            "setor": setores[0],
            "skill": None,
            "status": "ambiguo",
            "skills_candidatas": candidatas,
            "contexto_coletado": bool(contexto),
            "metodo": "multiplas_candidatas",
            "next_action": f"Qual destas? {', '.join(candidatas[:5])}"
        }
    else:
        resultado = {
            "intencao": intencao,
            "setor": setores[0] if setores else None,
            "skill": None,
            "status": "gap",
            "skills_candidatas": [],
            "contexto_coletado": bool(contexto),
            "metodo": "sem_candidatas",
            "next_action": f"Gap no setor {setores[0] or 'desconhecido'}. Criar skill?"
        }

    return resultado


if __name__ == "__main__":
    intencao = " ".join(sys.argv[1:]) or "bom dia"
    result = delegate(intencao)
    print(json.dumps(result, indent=2, ensure_ascii=False))
