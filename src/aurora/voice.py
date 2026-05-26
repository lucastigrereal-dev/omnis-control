"""AuroraVoice — Tom Tigre para insights da Aurora.

Adapta qualquer insight generico ao tom do Lucas Tigre:
  - Direto ao ponto (sem rodeios)
  - Ação IMEDIATA — Feito > Perfeito
  - Foco em dinheiro, leads e caixa AGORA
  - Nunca abstrato — sempre o próximo passo concreto
  - Curto: 1-3 frases max
  - Urgencia sem drama

Corpus: carrega data/voice_corpus.jsonl se disponivel.
Fallback: padroes embutidos (Tigre patterns).

Princípios:
- 100% local, sem Ollama, sem API
- dry_run=True como default
- Nunca lança excecao
- Interface estavel para KRATOS via to_dict()
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_logger = logging.getLogger("omnis.aurora.voice")

_DEFAULT_DATA_DIR = Path("data")
_CORPUS_FILE = "voice_corpus.jsonl"

# Max caracteres do output (resposta curta — TDAH friendly)
_MAX_OUTPUT_CHARS = 280


# ---------------------------------------------------------------------------
# Tom Tigre — Padrões de voz embutidos
# ---------------------------------------------------------------------------

# Substituicoes de palavras/frases genericas -> diretas (case-insensitive)
_REPLACEMENTS: list[tuple[str, str]] = [
    # Abstratos → concretos
    (r"[eé]\s+importante\s+considerar", "faz isso"),
    (r"[eé]\s+necess[aá]rio", "precisa"),
    (r"seria interessante", "faz"),
    (r"poderia ser útil", "usa"),
    (r"recomenda-se", "faz"),
    (r"sugere-se", "faz"),
    (r"talvez valha a pena", "vale"),
    (r"no futuro próximo", "hoje"),
    (r"em breve", "agora"),
    (r"eventualmente", "hoje"),
    (r"pode ajudar", "resolve"),
    (r"pode contribuir", "ajuda"),
    (r"seria benéfico", "gera resultado"),
    # Verbos fracos → fortes
    (r"tentar", "fazer"),
    (r"verificar se é possível", "testar"),
    (r"considerar a possibilidade de", ""),
    (r"pensar em", "fazer"),
    # Tempo → urgencia
    (r"semana que vem", "essa semana"),
    (r"nos próximos dias", "hoje"),
    (r"no próximo mês", "essa semana"),
]

# Frases de abertura Tigre (prefix rotativo por hash do texto)
_TIGRE_OPENERS: list[str] = [
    "Lucas, foca aqui:",
    "Caixa hoje:",
    "Direto ao ponto:",
    "Move agora:",
    "Oportunidade real:",
    "OMNIS detectou:",
    "Prioridade:",
]

# Sufixos de chamada para ação (CTA Tigre)
_TIGRE_CTAS: list[str] = [
    "Qual a proxima acao?",
    "Faz isso hoje.",
    "Feito > Perfeito.",
    "Move.",
    "Caixa primeiro.",
]

# Keywords que sinalizam oportunidade de dinheiro → enfatizar no tom
_MONEY_KW = ["hotel", "restaurante", "collab", "publi", "cliente", "lead",
             "r$", "reais", "receita", "venda", "contrato", "fee"]


@dataclass
class VoiceOutput:
    """Resultado do processamento de voz Tigre."""

    original: str           # texto original
    adapted: str            # texto no tom Tigre
    style: str              # "tigre" | "corpus" | "passthrough"
    has_money_signal: bool  # detectou sinal de dinheiro no texto
    generated_at: str       # ISO 8601

    def to_dict(self) -> dict:
        return {
            "original": self.original,
            "adapted": self.adapted,
            "style": self.style,
            "has_money_signal": self.has_money_signal,
            "generated_at": self.generated_at,
        }

    def __str__(self) -> str:
        return self.adapted


@dataclass
class VoiceCorpusEntry:
    """Uma entrada do corpus de voz (legenda ou frase do Lucas)."""

    text: str
    source: str = ""    # ex: "reels_2024", "caption_aprovada"
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"text": self.text, "source": self.source, "tags": self.tags}

    @classmethod
    def from_dict(cls, d: dict) -> "VoiceCorpusEntry":
        return cls(
            text=d.get("text", ""),
            source=d.get("source", ""),
            tags=d.get("tags", []),
        )


class AuroraVoice:
    """Adapta textos/insights ao tom Lucas Tigre.

    Uso:
        voice = AuroraVoice()
        out = voice.adapt("Seria interessante considerar fechar parcerias com hoteis.")
        print(out.adapted)
        # → "Caixa hoje: fecha parceria com hotel. Move."
    """

    def __init__(
        self,
        dry_run: bool = True,
        data_dir: Path = _DEFAULT_DATA_DIR,
    ) -> None:
        self.dry_run = dry_run
        self.data_dir = Path(data_dir)
        self._corpus: list[VoiceCorpusEntry] = []
        self._corpus_loaded = False

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def adapt(self, text: str) -> VoiceOutput:
        """Adapta um texto ao tom Tigre.

        Args:
            text: Insight ou texto generico a ser adaptado.

        Returns:
            VoiceOutput com texto adaptado e metadata.
            Se texto vazio → passthrough com aviso.
        """
        now = datetime.now(timezone.utc).isoformat()

        if not text or not text.strip():
            return VoiceOutput(
                original=text or "",
                adapted="(sem conteudo para adaptar)",
                style="passthrough",
                has_money_signal=False,
                generated_at=now,
            )

        text = text.strip()
        has_money = self._has_money_signal(text)

        # Aplica adaptacao Tigre
        adapted = self._apply_tigre_rules(text, has_money)

        return VoiceOutput(
            original=text,
            adapted=adapted,
            style="tigre",
            has_money_signal=has_money,
            generated_at=now,
        )

    def adapt_many(self, texts: list[str]) -> list[VoiceOutput]:
        """Adapta uma lista de textos. Retorna na mesma ordem."""
        return [self.adapt(t) for t in texts]

    def load_corpus(self) -> list[VoiceCorpusEntry]:
        """Carrega corpus de data/voice_corpus.jsonl (se existir).

        Retorna lista de entradas. Retorna [] se arquivo ausente.
        Nunca lança excecao.
        """
        if self._corpus_loaded:
            return self._corpus

        self._corpus_loaded = True
        corpus_path = self.data_dir / _CORPUS_FILE

        if not corpus_path.exists():
            _logger.debug(
                "aurora.voice: corpus ausente em %s — usando padroes Tigre",
                corpus_path,
            )
            return []

        entries: list[VoiceCorpusEntry] = []
        try:
            for i, line in enumerate(corpus_path.open(encoding="utf-8")):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    entries.append(VoiceCorpusEntry.from_dict(data))
                except (json.JSONDecodeError, KeyError) as exc:
                    _logger.debug(
                        "aurora.voice: linha %d invalida no corpus (%s) — ignorada", i, exc
                    )
        except Exception as exc:  # noqa: BLE001
            _logger.warning("aurora.voice: falha ao ler corpus: %s", exc)

        self._corpus = entries
        _logger.debug(
            "aurora.voice: corpus carregado — %d entradas", len(entries)
        )
        return entries

    def corpus_stats(self) -> dict:
        """Retorna estatísticas do corpus carregado."""
        entries = self.load_corpus()
        sources = {}
        for e in entries:
            sources[e.source] = sources.get(e.source, 0) + 1
        return {
            "total_entries": len(entries),
            "sources": sources,
            "corpus_path": str(self.data_dir / _CORPUS_FILE),
        }

    # ------------------------------------------------------------------
    # Privado — adaptacao Tigre
    # ------------------------------------------------------------------

    def _apply_tigre_rules(self, text: str, has_money: bool) -> str:
        """Aplica regras de voz Tigre ao texto."""
        # 1. Substituicoes lexicais
        adapted = self._lexical_replace(text)

        # 2. Trunca para maximo de chars (TDAH friendly)
        adapted = self._truncate(adapted)

        # 3. Adiciona prefixo Tigre (rotativo por hash do texto)
        opener = self._pick_opener(text, has_money)

        # 4. Adiciona CTA Tigre
        cta = self._pick_cta(text)

        # Monta saída
        if opener and not adapted.lower().startswith(opener.lower().rstrip(":")):
            adapted = f"{opener} {adapted}"

        # Garante que termina com ponto
        adapted = adapted.rstrip()
        if adapted and adapted[-1] not in ".!?":
            adapted += "."

        # Adiciona CTA separado
        adapted = f"{adapted} {cta}"

        return adapted

    @staticmethod
    def _lexical_replace(text: str) -> str:
        """Substitui expressoes genericas por equivalentes diretos."""
        result = text
        for pattern, replacement in _REPLACEMENTS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        # Remove espacos duplos após substituicao
        result = re.sub(r"\s{2,}", " ", result).strip()
        return result

    @staticmethod
    def _truncate(text: str, max_chars: int = _MAX_OUTPUT_CHARS) -> str:
        """Trunca em limite de chars, preservando sentença completa."""
        if len(text) <= max_chars:
            return text
        # Tenta cortar na última frase completa dentro do limite
        truncated = text[:max_chars]
        last_period = max(
            truncated.rfind("."),
            truncated.rfind("!"),
            truncated.rfind("?"),
        )
        if last_period > max_chars * 0.5:
            return truncated[: last_period + 1]
        return truncated.rstrip() + "..."

    @staticmethod
    def _has_money_signal(text: str) -> bool:
        """Detecta se o texto menciona dinheiro/leads/caixa."""
        text_lower = text.lower()
        return any(kw in text_lower for kw in _MONEY_KW)

    @staticmethod
    def _pick_opener(text: str, has_money: bool) -> str:
        """Seleciona prefixo Tigre baseado no conteudo."""
        if has_money:
            return "Caixa hoje:"
        # Rotativo por hash simples
        idx = abs(hash(text)) % len(_TIGRE_OPENERS)
        return _TIGRE_OPENERS[idx]

    @staticmethod
    def _pick_cta(text: str) -> str:
        """Seleciona CTA Tigre baseado no conteudo."""
        idx = abs(hash(text[:20])) % len(_TIGRE_CTAS)
        return _TIGRE_CTAS[idx]
