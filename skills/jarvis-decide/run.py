#!/usr/bin/env python3
"""jarvis-decide: Decision Engine — prioriza oportunidades usando fórmula composta."""

import json
import os
import sys
from typing import Optional
import yaml

DECISION_ENGINE_PATH = os.path.expanduser("~/.claude/registry/decision_engine.yaml")

FACTOR_KEYS = ["receita", "desbloqueio", "chance", "urgencia",
               "reaproveitamento", "energia", "risco", "complexidade"]

DEFAULT_WEIGHTS = {
    "receita": 0.30, "desbloqueio": 0.20, "chance": 0.15,
    "urgencia": 0.15, "reaproveitamento": 0.10, "energia": 0.05,
    "risco": -0.10, "complexidade": -0.10,
}


def carregar_pesos() -> dict:
    """Carrega pesos do decision_engine.yaml."""
    try:
        if os.path.exists(DECISION_ENGINE_PATH):
            with open(DECISION_ENGINE_PATH) as f:
                data = yaml.safe_load(f)
            factors = data.get("formula", {}).get("factors", [])
            return {f["name"]: f["weight"] for f in factors}
    except Exception:
        pass
    return DEFAULT_WEIGHTS


def calcular_score(oportunidade: dict, weights: dict) -> float:
    """Calcula score composto para uma oportunidade."""
    score = 0.0
    for key, weight in weights.items():
        valor = float(oportunidade.get(key, 0))
        score += valor * weight
    return round(score, 2)


def classificar(score: float, thresholds: Optional[dict] = None) -> str:
    """Classifica o score em recomendação."""
    if thresholds is None:
        thresholds = {"auto_executar": 7.0, "sugerir": 4.0}
    if score >= thresholds.get("auto_executar", 7.0):
        return "executar"
    if score >= thresholds.get("sugerir", 4.0):
        return "sugerir"
    return "ignorar"


def decide(oportunidades: list[dict]) -> dict:
    """Pipeline principal: calcula scores e rankeia."""
    if not oportunidades:
        return {"status": "empty", "ranking": [], "recomendacao": "Nenhuma oportunidade para avaliar"}

    weights = carregar_pesos()

    # Calcular scores
    for i, opp in enumerate(oportunidades):
        if "id" not in opp:
            opp["id"] = f"opcao_{i+1}"
        opp["score"] = calcular_score(opp, weights)
        opp["recomendacao"] = classificar(opp["score"])

    # Ordenar por score (decrescente)
    ranked = sorted(oportunidades, key=lambda x: x["score"], reverse=True)

    # Adicionar rank
    for i, opp in enumerate(ranked):
        opp["rank"] = i + 1

    top = ranked[0] if ranked else None
    recomendacao = f"#{top['rank']} {top.get('id', 'N/A')} (score: {top['score']})" if top else "Nada"

    return {
        "status": "ok",
        "ranking": ranked,
        "total_avaliadas": len(ranked),
        "recomendacao": recomendacao,
        "next_action": f"Executar {recomendacao}?"
    }


if __name__ == "__main__":
    oportunidades = [
        {"id": "Enviar DM para Hotel Majestic", "receita": 8, "desbloqueio": 3, "chance": 7, "urgencia": 6, "reaproveitamento": 5, "energia": 7, "risco": 1, "complexidade": 2},
        {"id": "Criar carrossel @oinatalrn", "receita": 5, "desbloqueio": 2, "chance": 9, "urgencia": 4, "reaproveitamento": 8, "energia": 6, "risco": 1, "complexidade": 3},
        {"id": "Organizar PC (duplicados)", "receita": 1, "desbloqueio": 4, "chance": 10, "urgencia": 2, "reaproveitamento": 3, "energia": 4, "risco": 2, "complexidade": 6},
    ]

    if len(sys.argv) > 1:
        try:
            oportunidades = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            pass

    result = decide(oportunidades)
    print(json.dumps(result, indent=2, ensure_ascii=False))
