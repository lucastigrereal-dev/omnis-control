"""AuroraThinker — pensador local da Aurora v1.

Lê os dados reais do OMNIS (state.json + fila + último run),
envia para Ollama local e devolve insight em português.
Custo: ZERO (100% Ollama local). Nunca chama API paga.

Saída esperada: dict com aurora_insight (str) + aurora_updated_at (ISO).
"""
from __future__ import annotations

import json
import logging
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.aurora.context_engine import AuroraContext, ContextEngine

_logger = logging.getLogger("omnis.aurora.thinker")

_OLLAMA_BASE = "http://localhost:11434"
_DEFAULT_MODEL = "llama3.1:8b"   # melhor qualidade em PT-BR

_SYSTEM_PROMPT = (
    "Você é Aurora, assistente de operações do Lucas Tigre — criador de conteúdo "
    "com 2.3 milhões de seguidores em 6 perfis do Instagram (viagem, gastronomia, família). "
    "Analise os dados do sistema OMNIS e escreva em 2-3 frases qual é o foco do dia e por quê. "
    "Tom: direto, sem enrolação, como um briefing de negócio. "
    "Responda APENAS com o texto do insight, sem títulos, sem listas, sem explicações extras."
)

_USER_TEMPLATE = """\
Dados do OMNIS hoje ({date}):

SISTEMA:
- Missão ativa: {active_mission}
- Status do último run: {last_run_status}
- Workflows registrados: {workflows}
- Testes passando: {test_count}
- Branch: {branch}

COMERCIAL (leads reais):
{leads_summary}

CONTEÚDO:
- Posts na fila de publicação: {queue_count}

ÚLTIMO RUN:
- Pedido: {last_run_request}
- Resultado: {last_run_result}

Em 2-3 frases, qual é o foco de hoje para o Lucas e por quê?"""


@dataclass
class AuroraInsight:
    insight: str
    updated_at: str
    model_used: str
    tokens_used: int
    data_snapshot: dict

    def to_dict(self) -> dict:
        return {
            "aurora_insight": self.insight,
            "aurora_updated_at": self.updated_at,
            "aurora_model": self.model_used,
            "aurora_tokens": self.tokens_used,
        }


def write_insight_to_state(
    insight: "AuroraInsight",
    data_dir: Path = Path("data"),
) -> Path:
    """Mescla os campos aurora_* no state.json SEM clobberar chaves existentes.

    Lê o state.json atual (ou {} se ausente/inválido), adiciona/atualiza apenas
    as chaves aurora_insight, aurora_updated_at, aurora_model, aurora_tokens,
    e grava de volta. Preserva timestamp, test_count, branch, etc.

    Retorna o caminho gravado. Escreve apenas em state.json (não em runtime jsonl).
    """
    state_path = Path(data_dir) / "state.json"

    current: dict = {}
    if state_path.exists():
        try:
            current = json.loads(state_path.read_text(encoding="utf-8")) or {}
        except (json.JSONDecodeError, OSError):
            current = {}

    current.update(insight.to_dict())

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(current, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    _logger.info("aurora.write: state.json atualizado com aurora_insight (%s)", state_path)
    return state_path


class AuroraThinker:
    """Pensador mínimo da Aurora — Ollama local, dados reais, zero custo."""

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        base_url: str = _OLLAMA_BASE,
        data_dir: Path = Path("data"),
    ) -> None:
        self.model = model
        self.base_url = base_url
        self.data_dir = Path(data_dir)

    def health_check(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=3):
                return True
        except (urllib.error.URLError, OSError):
            return False

    def _load_data(self) -> dict:
        """Lê dados reais disponíveis — falha graciosa se arquivo ausente."""
        snapshot: dict = {}

        # 1 — state.json
        state_path = self.data_dir / "state.json"
        if state_path.exists():
            try:
                snapshot["state"] = json.loads(state_path.read_text(encoding="utf-8"))
            except Exception:
                snapshot["state"] = {}

        # 2 — content_queue.jsonl (contagem simples)
        queue_path = self.data_dir / "content_queue.jsonl"
        if queue_path.exists():
            try:
                snapshot["queue_count"] = sum(1 for _ in queue_path.open(encoding="utf-8"))
            except Exception:
                snapshot["queue_count"] = 0
        else:
            snapshot["queue_count"] = 0

        # 3 — último orchestrator run
        runs_path = self.data_dir / "orchestrator_runs.jsonl"
        snapshot["last_run"] = {}
        if runs_path.exists():
            try:
                lines = [l for l in runs_path.read_text(encoding="utf-8").strip().split("\n") if l]
                if lines:
                    snapshot["last_run"] = json.loads(lines[-1])
            except Exception:
                pass

        # 4 — leads consultáveis (data/leads.jsonl)
        # Formato: {nome, perfil, temperatura, ultimo_contato, valor_potencial, status}
        leads_path = self.data_dir / "leads.jsonl"
        snapshot["leads"] = []
        if leads_path.exists():
            try:
                for line in leads_path.open(encoding="utf-8"):
                    line = line.strip()
                    if line:
                        try:
                            snapshot["leads"].append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
            except Exception:
                pass

        # 5 — Context Engine (Notion + Akasha quando disponíveis via env vars)
        # Sempre roda; fontes opcionais retornam [] se não configuradas.
        try:
            engine = ContextEngine(data_dir=self.data_dir)
            ctx = engine.build(query="leads hoteis publicidade receita")
            snapshot["context_results"] = ctx.results
            snapshot["context_sources"] = ctx.sources_available
            snapshot["context_failed"] = ctx.sources_failed
        except Exception as exc:  # noqa: BLE001
            _logger.warning("aurora._load_data: context_engine falhou (%s) — ignorado", exc)
            snapshot["context_results"] = []
            snapshot["context_sources"] = []
            snapshot["context_failed"] = []

        return snapshot

    # Statuses que são ruído de automação de testes — não representam bloqueio real
    _NOISE_STATUSES = frozenset({
        "blocked_pending_approval",  # 6.189 approval_requests são artefatos de pytest
    })

    def _build_prompt(self, snapshot: dict) -> str:
        state = snapshot.get("state", {})
        last_run = snapshot.get("last_run", {})

        # Status do último run — filtra ruído de automação
        raw_status = last_run.get("status", "sem dados")
        if raw_status in self._NOISE_STATUSES:
            last_run_status = "aguardando_proxima_missao (aprovacoes pendentes sao ruido de testes)"
        else:
            last_run_status = raw_status

        blockers = last_run.get("blockers", [])
        last_run_result = last_run_status
        if blockers:
            last_run_result = f"{last_run_status} — {blockers[0]}"

        # Estado do sistema — também filtra o status stale do state.json
        sys_run_status = state.get("last_run_status", "desconhecido")
        if sys_run_status in self._NOISE_STATUSES:
            sys_run_status = "pipeline_ativo (sem bloqueio real)"

        # Leads summary
        leads_summary = self._build_leads_summary(snapshot.get("leads", []))

        base_prompt = _USER_TEMPLATE.format(
            date=datetime.now().strftime("%d/%m/%Y"),
            active_mission=state.get("active_mission_title", "sem missão ativa"),
            last_run_status=sys_run_status,
            workflows=state.get("workflows_registered", "?"),
            test_count=state.get("test_count", "?"),
            branch=state.get("branch", "?"),
            leads_summary=leads_summary,
            queue_count=snapshot.get("queue_count", 0),
            last_run_request=last_run.get("request_text", "sem dados")[:120],
            last_run_result=last_run_result,
        )

        # Seção CONTEXTO EXTERNO — inclusa apenas se ContextEngine trouxe dados extras
        # (Notion ou Akasha ativos). Fontes state_json e leads já aparecem acima.
        external_results = [
            r for r in snapshot.get("context_results", [])
            if r.source not in ("state_json", "leads")
        ]
        if external_results:
            lines = ["\nCONTEXTO EXTERNO (Notion/Akasha):"]
            for r in external_results[:5]:  # máximo 5 itens para não inflar o prompt
                lines.append(f"- [{r.source}] {r.content[:200]}")
            base_prompt += "\n".join(lines)

        return base_prompt

    @staticmethod
    def _build_leads_summary(leads: list[dict]) -> str:
        """Gera resumo de leads para o prompt da Aurora."""
        if not leads:
            return "- Nenhum lead cadastrado ainda (leads.jsonl vazio)"

        quente = [l for l in leads if l.get("temperatura") == "quente"]
        morno = [l for l in leads if l.get("temperatura") == "morno"]
        frio = [l for l in leads if l.get("temperatura") == "frio"]

        lines = [f"- Total: {len(leads)} leads | Quente: {len(quente)} | Morno: {len(morno)} | Frio: {len(frio)}"]

        # Top 3 quentes
        if quente:
            lines.append("- Leads QUENTES (ação imediata):")
            for lead in quente[:3]:
                valor = lead.get("valor_potencial", "?")
                ultimo = lead.get("ultimo_contato", "?")
                lines.append(
                    f"  * {lead.get('nome','?')} ({lead.get('perfil','?')}) | "
                    f"R${valor} | Último contato: {ultimo} | Status: {lead.get('status','?')}"
                )
        elif morno:
            lines.append("- Sem leads quentes. Top morno:")
            lead = morno[0]
            lines.append(
                f"  * {lead.get('nome','?')} ({lead.get('perfil','?')}) | "
                f"R${lead.get('valor_potencial','?')} | Status: {lead.get('status','?')}"
            )

        return "\n".join(lines)

    def _call_ollama(self, user_prompt: str) -> tuple[str, int]:
        """Chama Ollama e retorna (texto_insight, tokens_usados)."""
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 300,
            "temperature": 0.5,
            "stream": False,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())

        content = data["choices"][0]["message"]["content"].strip()
        tokens = data.get("usage", {}).get("total_tokens", 0)
        return content, tokens

    def think(self) -> AuroraInsight:
        """Roda o ciclo completo: lê dados → prompt → Ollama → insight."""
        if not self.health_check():
            raise RuntimeError("Ollama não está respondendo em http://localhost:11434")

        _logger.info("aurora.think: carregando dados reais...")
        snapshot = self._load_data()

        user_prompt = self._build_prompt(snapshot)
        _logger.info("aurora.think: enviando para Ollama modelo=%s...", self.model)

        insight_text, tokens = self._call_ollama(user_prompt)
        updated_at = datetime.now(timezone.utc).isoformat()

        _logger.info("aurora.think: insight gerado, tokens=%d", tokens)

        return AuroraInsight(
            insight=insight_text,
            updated_at=updated_at,
            model_used=self.model,
            tokens_used=tokens,
            data_snapshot=snapshot,
        )
