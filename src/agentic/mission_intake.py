"""MissionIntake — extrai objetivo, setor, tipo, prazo e risco de texto livre."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


SECTOR_KEYWORDS: dict[str, list[str]] = {
    "marketing": [
        "hotel", "campanha", "post", "carrossel", "legenda", "calendario",
        "conteudo", "instagram", "reel", "video", "publicar", "postar",
        "story", "stories", "feed", "engajamento", "seguidor", "caption",
        "influencer", "divulgar", "divulgacao", "promocao", "promover",
    ],
    "sales": [
        "lead", "venda", "proposta", "cliente", "dm", "comercial",
        "contrato", "negocio", "fechar", "comissao", "pipeline",
        "crm", "prospeccao", "prospect", "sdr", "outreach",
    ],
    "app_factory": [
        "app", "aplicativo", "sistema", "codigo", "prd", "api",
        "schema", "frontend", "backend", "teste", "deploy", "build",
        "feature", "bug", "fix", "refatorar",
    ],
    "computer_ops": [
        "disco", "audit", "saude", "health", "organizar", "backup",
        "quarentena", "limpar", "arquivo", "pasta", "worktree",
    ],
    "finance": [
        "financeiro", "preco", "precificacao", "custo", "receita",
        "faturamento", "orcamento", "lucro", "margem", "roi",
        "pagamento", "cobrar", "nota fiscal",
    ],
}

TYPE_PATTERNS: list[tuple[str, list[str]]] = [
    ("campaign", ["campanha", "calendario", "promocao", "lancamento", "divulgar"]),
    ("sales", ["lead", "venda", "proposta", "cliente", "comercial", "prospeccao", "fechar negocio"]),
    ("content", ["post", "carrossel", "legenda", "reel", "video", "caption", "story", "stories", "conteudo"]),
    ("ops", ["audit", "health", "saude", "organizar", "backup", "limpar", "quarentena"]),
    ("dev", ["app", "codigo", "prd", "api", "schema", "build", "deploy", "feature", "bug", "refatorar"]),
    ("finance", ["preco", "precificacao", "custo", "receita", "orcamento", "financeiro", "roi"]),
]

RISK_KEYWORDS: dict[str, list[str]] = {
    "alto": ["apagar", "deletar", "remover", "excluir", "drop", "reset", "destrutivo"],
    "medio": ["deploy", "publicar", "postar", "push", "email", "enviar", "prod", "producao"],
}


def _find_date(text: str) -> Optional[str]:
    lower = text.lower()
    if any(w in lower for w in ["urgente", "hoje", "agora", "imediatamente"]):
        return _today()
    if "amanha" in lower or "amanhã" in lower:
        return (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    m = re.search(r"(\d+)\s*dias?", lower)
    if m:
        days = int(m.group(1))
        return (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%d")
    m = re.search(r"(\d{2})/(\d{2})(?:/(\d{4}))?", text)
    if m:
        d, mo = int(m.group(1)), int(m.group(2))
        y = int(m.group(3)) if m.group(3) else datetime.now(timezone.utc).year
        try:
            return datetime(y, mo, d).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def _classify(text_lower: str, keyword_map: dict[str, list[str]]) -> str:
    scores: dict[str, int] = {}
    for label, keywords in keyword_map.items():
        scores[label] = sum(1 for kw in keywords if kw in text_lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


@dataclass
class MissionIntakeResult:
    objetivo: str
    setor: str = "general"
    tipo: str = "general"
    risco: str = "baixo"
    prazo: Optional[str] = None
    texto_original: str = ""
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "objetivo": self.objetivo,
            "setor": self.setor,
            "tipo": self.tipo,
            "risco": self.risco,
            "prazo": self.prazo,
            "texto_original": self.texto_original,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MissionIntakeResult":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class MissionIntake:
    """Analisa texto livre e extrai campos estruturados da missão."""

    def parse(self, text: str) -> MissionIntakeResult:
        """Extrai objetivo, setor, tipo, prazo e risco do texto bruto."""
        clean = text.strip()
        lower = clean.lower()

        setor = _classify(lower, SECTOR_KEYWORDS)
        tipo = _classify(lower, {k: v for k, v in TYPE_PATTERNS})
        prazo = _find_date(clean)
        risco = self._classify_risco(lower)
        objetivo = self._clean_objetivo(clean)
        warnings = self._build_warnings(risco, prazo)

        return MissionIntakeResult(
            objetivo=objetivo,
            setor=setor,
            tipo=tipo,
            risco=risco,
            prazo=prazo,
            texto_original=clean,
            warnings=warnings,
        )

    def _clean_objetivo(self, text: str) -> str:
        """Normaliza o objetivo removendo ruído."""
        return text.strip().strip('"').strip("'")

    def _classify_risco(self, text_lower: str) -> str:
        if any(kw in text_lower for kw in RISK_KEYWORDS["alto"]):
            return "alto"
        if any(kw in text_lower for kw in RISK_KEYWORDS["medio"]):
            return "medio"
        return "baixo"

    def _build_warnings(self, risco: str, prazo: Optional[str]) -> list[str]:
        w: list[str] = []
        if risco == "alto":
            w.append("risco alto — requer aprovação antes de executar")
        if prazo and prazo == _today():
            w.append("prazo urgente — ação imediata necessária")
        return w


def _classify(text_lower: str, keyword_map: dict[str, list[str]]) -> str:
    scores: dict[str, int] = {}
    for label, keywords in keyword_map.items():
        scores[label] = sum(1 for kw in keywords if kw in text_lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"
