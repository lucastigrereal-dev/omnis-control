"""core/agents/config.py — Configurações canônicas dos 12 agentes OMNIS.

Cada agente declara seu default_model (nome lógico LiteLLM).
Política v2.1 Quality-First — todos via proxy :4001.

Mudanças v2.0 → v2.1:
  - SDR:        ollama-fast  → ollama-code   (kimi-k2.6 ⚠️ MUDOU)
  - Aurora:     ollama-smart → ollama-code   (kimi-k2.6 ⚠️ MUDOU)
  - AppFactory: ollama-code  → ollama-build  (minimax-m2.7 ⚠️ MUDOU)
  - ACaixa:     (novo)       → ollama-longctx (minimax-m2.7)

Referência: https://www.notion.so/36d22eba8f088199a2d6cf5a7e958cee
"""
from __future__ import annotations

from dataclasses import dataclass

from core.llm.router import (
    OLLAMA_BACKUP,
    OLLAMA_BUILD,
    OLLAMA_CODE,
    OLLAMA_FAST,
    OLLAMA_LONGCTX,
    OLLAMA_SMART,
)


@dataclass(frozen=True)
class AgentConfig:
    """Configuração mínima de um agente OMNIS."""
    name: str
    default_model: str
    description: str


# ── Tabela canônica dos 12 agentes ────────────────────────────────────────

AGENT_CONFIGS: dict[str, AgentConfig] = {
    "secretaria": AgentConfig(
        name="secretaria",
        default_model=OLLAMA_FAST,      # glm-5.1:cloud
        description="Roteamento, triagem e operações de volume (~70% das chamadas)",
    ),
    "operacional": AgentConfig(
        name="operacional",
        default_model=OLLAMA_FAST,      # glm-5.1:cloud
        description="Execução de tarefas operacionais e automações",
    ),
    "conteudo": AgentConfig(
        name="conteudo",
        default_model=OLLAMA_FAST,      # glm-5.1:cloud
        description="Geração de captions, hooks e conteúdo de feed",
    ),
    "design": AgentConfig(
        name="design",
        default_model=OLLAMA_FAST,      # glm-5.1:cloud
        description="Briefings de design e diretivas visuais",
    ),
    "sdr": AgentConfig(
        name="sdr",
        default_model=OLLAMA_CODE,      # kimi-k2.6:cloud ⚠️ MUDOU v2.1
        description="Prospecção de leads, análise de hotéis e restaurantes",
    ),
    "arquivo": AgentConfig(
        name="arquivo",
        default_model=OLLAMA_FAST,      # glm-5.1:cloud
        description="Gestão de assets, indexação e recuperação",
    ),
    "performance": AgentConfig(
        name="performance",
        default_model=OLLAMA_SMART,     # deepseek-v4-pro:cloud
        description="Análise de métricas, insights e otimização de alcance",
    ),
    "inteligencia": AgentConfig(
        name="inteligencia",
        default_model=OLLAMA_SMART,     # deepseek-v4-pro:cloud
        description="Raciocínio profundo, planejamento estratégico e decisão",
    ),
    "sprint_orchestrator": AgentConfig(
        name="sprint_orchestrator",
        default_model=OLLAMA_FAST,      # glm-5.1:cloud
        description="Orquestração de sprints e coordenação de waves",
    ),
    "aurora": AgentConfig(
        name="aurora",
        default_model=OLLAMA_CODE,      # kimi-k2.6:cloud ⚠️ MUDOU v2.1 (era ollama-smart)
        description="Interpretação, orientação e voz do OMNIS",
    ),
    "app_factory": AgentConfig(
        name="app_factory",
        default_model=OLLAMA_BUILD,     # minimax-m2.7:cloud ⚠️ MUDOU v2.1 (era ollama-code)
        description="Geração de código, scaffolding e builds completos",
    ),
    "acaixa": AgentConfig(
        name="acaixa",
        default_model=OLLAMA_LONGCTX,  # minimax-m2.7:cloud — NOVO papel v2.1
        description="RAG de contexto longo, Akasha e análise de documentos extensos",
    ),
}


def get_model(agent_name: str) -> str:
    """Retorna o default_model para o agente informado.

    Args:
        agent_name: Nome do agente (case-insensitive).

    Returns:
        Nome lógico do modelo LiteLLM.

    Raises:
        KeyError: Se agente não registrado.
    """
    key = agent_name.lower()
    config = AGENT_CONFIGS.get(key)
    if config is None:
        raise KeyError(
            f"Agente '{agent_name}' não registrado. "
            f"Agentes disponíveis: {sorted(AGENT_CONFIGS.keys())}"
        )
    return config.default_model
