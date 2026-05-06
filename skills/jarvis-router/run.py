#!/usr/bin/env python3
"""jarvis-router: Classifica intenção do usuário em intenção + setor usando LLM leve (Haiku)."""

import json
import os
import re
import sys
from typing import Optional
from urllib.request import Request, urlopen

SECTORS = {
    "midia_conteudo": ["conteudo", "post", "legenda", "reel", "carrossel", "instagram", "publicar", "hashtag",
                       "video", "foto", "story", "agendar", "seogram", "hub", "midia"],
    "comercial_sdr": ["hotel", "pousada", "prospectar", "vender", "publi", "collab", "dm", "sdr",
                      "parceria", "cliente", "patrocinio", "anunciante", "hospedagem"],
    "vendas_crm": ["crm", "pipeline", "lead", "fechar", "proposta", "orcamento", "faturamento",
                   "contrato", "cliente_ativo", "renovacao", "upsell"],
    "conhecimento_inteligencia": ["buscar", "pesquisar", "saber", "conhecimento", "biblioteca", "livro",
                                  "insight", "akasha", "aprender", "estudar", "duvida", "o que e"],
    "produto_tecnologia": ["app", "codigo", "deploy", "docker", "github", "server", "dev", "programar",
                           "tecnologia", "sistema", "bug", "funcao", "feature"],
    "financeiro_metricas": ["faturamento", "receita", "mrr", "roi", "custo", "lucro", "gasto",
                            "dinheiro", "quanto", "investimento", "retorno", "meta"],
    "operacoes_organizacao": ["organizar", "arrumar", "status", "diagnostico", "rotina", "tarefa",
                              "o que fazer", "prioridade", "checklist", "limpar", "duplicado"],
}

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LITELLM_URL = os.getenv("LITELLM_URL", "http://localhost:4002")
LITELLM_KEY = os.getenv("LITELLM_KEY", "")


def classificar_llm(text: str) -> Optional[dict]:
    """Tenta classificar via LiteLLM (Haiku ou equivalente mais barato)."""
    payload = json.dumps({
        "model": "claude-haiku-4.5" if LITELLM_KEY else "local-fast",
        "messages": [{
            "role": "user",
            "content": f"""Classifique a mensagem abaixo em UM dos 7 setores e extraia entidades.

Mensagem: "{text}"

Responda APENAS com JSON:
{{"intent":"comando|pergunta|relato|decisao|desconhecido","sector":"midia_conteudo|comercial_sdr|vendas_crm|conhecimento_inteligencia|produto_tecnologia|financeiro_metricas|operacoes_organizacao","confidence":0.0-1.0,"entities":[],"text_summary":"max 8 palavras"}}"""
        }],
        "temperature": 0.1,
        "max_tokens": 150
    }).encode()

    try:
        req = Request(f"{LITELLM_URL}/chat/completions", data=payload,
                      headers={"Content-Type": "application/json"})
        if LITELLM_KEY:
            req.add_header("Authorization", f"Bearer {LITELLM_KEY}")
        resp = urlopen(req, timeout=5)
        result = json.loads(resp.read())
        content = result["choices"][0]["message"]["content"]
        return json.loads(re.sub(r'^```(?:json)?\s*|\s*```$', '', content.strip()))
    except Exception:
        return None


def classificar_heuristico(text: str) -> dict:
    """Fallback: classificação por keyword matching."""
    text_lower = text.lower()
    scores = {}

    for sector, keywords in SECTORS.items():
        score = sum(1 for kw in keywords if kw in text_lower) / max(len(keywords), 1)
        scores[sector] = min(score * 10, 0.95)

    best_sector = max(scores, key=scores.get)
    best_score = scores[best_sector]

    # Detectar intent básico
    if any(w in text_lower for w in ["?", "quem", "o que", "como", "qual", "onde", "por que"]):
        intent = "pergunta"
    elif any(w in text_lower for w in ["faz", "cria", "gera", "manda", "executa", "roda", "post",
                                        "organiza", "prospecta", "busca", "salva"]):
        intent = "comando"
    elif any(w in text_lower for w in ["decidi", "vou", "fechei", "mudei"]):
        intent = "decisao"
    elif any(w in text_lower for w in ["ontem", "hoje", "aconteceu", "recebi", "falei"]):
        intent = "relato"
    else:
        intent = "desconhecido"

    return {
        "intent": intent,
        "sector": best_sector if best_score > 0.15 else "operacoes_organizacao",
        "confidence": round(best_score, 2),
        "entities": [],
        "text_summary": " ".join(text.split()[:8]),
    }


def router(text: str) -> dict:
    """Pipeline principal: tenta LLM, fallback heurístico."""
    if not text or not text.strip():
        return {"intent": "desconhecido", "sector": "operacoes_organizacao",
                "confidence": 0.0, "entities": [], "text_summary": "",
                "next_action": "classificar", "error": "texto vazio"}

    result = classificar_llm(text)

    if result is None:
        result = classificar_heuristico(text)

    confidence = float(result.get("confidence", 0))
    if confidence >= 0.60:
        result["next_action"] = "buscar_contexto"
    elif confidence >= 0.20:
        result["next_action"] = "perguntar"
    else:
        result["next_action"] = "classificar"

    result["error"] = None
    return result


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) or "bom dia"
    result = router(text)
    print(json.dumps(result, indent=2, ensure_ascii=False))
