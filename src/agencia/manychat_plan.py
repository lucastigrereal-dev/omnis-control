"""ManychatPlanner — Gera plano de automação ManyChat para DMs de Instagram.

NUNCA envia DMs reais. Apenas gera um arquivo JSON estruturado para o Lucas
configurar manualmente no painel ManyChat.

Saída: data/manychat_plans/<date>-<plan_id>/plan.json

Conceitos:
- ManychatTrigger: palavra-chave que dispara o fluxo (ex: "QUERO" num comentário)
- ManychatSequencia: sequência de mensagens de nurturing (7 ou 30 dias)
- ManychatPlan: plano completo com triggers + sequências por perfil

Princípios:
- dry_run=True como padrão universal
- Salva plan.json SEMPRE (mesmo em dry_run)
- Nunca chama API ManyChat real
- Templates de mensagem por perfil e tipo de post
- Segmentação por tipo de post (hotel, restaurante, praia)
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_logger = logging.getLogger("omnis.agencia.manychat_plan")

_ROOT = Path(os.getenv("OMNIS_ROOT", os.path.expanduser("~/omnis-control")))
_DEFAULT_OUT = Path("data/manychat_plans")

# ------------------------------------------------------------------
# Templates de mensagem por perfil
# ------------------------------------------------------------------

_TEMPLATES: dict[str, dict[str, str]] = {
    "oinatalrn": {
        "hotel":       "Oi! Vi que você se interessou pelo hotel em Natal. Manda mensagem que te passo o contato direto! 🏨",
        "restaurante": "Oi! Esse restaurante em Natal é incrível mesmo. Quer saber mais? Clica aqui: {{link}}",
        "praia":       "Oi! Natal tem as melhores praias né? Te mando um guia completo, só clicar: {{link}}",
        "default":     "Oi! Vi seu interesse no post sobre Natal. Posso te ajudar com mais informações! Clica: {{link}}",
    },
    "lucastigrereal": {
        "hotel":       "E aí! Esse hotel é parceiro meu. Quer desconto exclusivo? Me manda 'QUERO' aqui: {{link}}",
        "restaurante": "Que bom que curtiu! Esse restaurante é top. Link com reserva: {{link}}",
        "praia":       "Viagem marcada? Te mando roteiro completo. Clica aqui: {{link}}",
        "default":     "Oi! Obrigado pelo interesse. Te mando mais detalhes: {{link}}",
    },
    "agenteviajabrasil": {
        "hotel":       "Oi viajante! Esse hotel tem condições especiais para seguidores. Confere: {{link}}",
        "restaurante": "Boa pedida esse restaurante! Guia completo de gastronomia aqui: {{link}}",
        "praia":       "Praia incrível né? Roteiro completo de praias brasileiras: {{link}}",
        "default":     "Oi! Obrigado pelo interesse. Mais informações aqui: {{link}}",
    },
    "afamiliatigrereal": {
        "hotel":       "Família reunida é tudo! Esse hotel é perfeito pra famílias. Saiba mais: {{link}}",
        "restaurante": "Que restaurante gostoso! Bom pra toda a família. Confere: {{link}}",
        "praia":       "Praia com família é um charme! Dicas completas aqui: {{link}}",
        "default":     "Oi! Que bom ver você por aqui. Mais detalhes: {{link}}",
    },
    "oquecomernatalrn": {
        "hotel":       "Hospedagem e gastronomia em Natal! Parceiro especial aqui: {{link}}",
        "restaurante": "Esse restaurante é sensacional! Cardápio e reserva aqui: {{link}}",
        "praia":       "Praia e boa comida em Natal! Guia completo: {{link}}",
        "default":     "Oi! Guia gastronômico de Natal completo: {{link}}",
    },
    "natalaivoueu": {
        "hotel":       "Natal te espera! Esse hotel é um dos melhores. Reserva aqui: {{link}}",
        "restaurante": "Gastronomia de Natal no seu melhor! Mais aqui: {{link}}",
        "praia":       "As praias de Natal são únicas! Roteiro completo: {{link}}",
        "default":     "Oi! Tudo sobre Natal aqui: {{link}}",
    },
    "default": {
        "hotel":       "Oi! Esse hotel é incrível. Quer saber mais? Clica: {{link}}",
        "restaurante": "Oi! Esse restaurante é uma ótima escolha. Confere: {{link}}",
        "praia":       "Oi! Que praia maravilhosa né? Mais dicas aqui: {{link}}",
        "default":     "Oi! Vi que você se interessou. Mais informações aqui: {{link}}",
    },
}

# ------------------------------------------------------------------
# Detecção de tipo de post a partir da caption
# ------------------------------------------------------------------

_POST_TYPE_KEYWORDS: dict[str, list[str]] = {
    "hotel":       ["hotel", "hospedagem", "resort", "pousada", "suíte", "suite", "quarto", "diária"],
    "restaurante": ["restaurante", "gastronomia", "cardápio", "prato", "chef", "culinária", "comida", "almoço", "jantar"],
    "praia":       ["praia", "mar", "litoral", "areia", "surf", "mergulho", "dunas", "piscina natural"],
}


def _detect_post_type(caption: str) -> str:
    """Detecta tipo de post a partir da caption (hotel|restaurante|praia|default)."""
    caption_lower = (caption or "").lower()
    for tipo, keywords in _POST_TYPE_KEYWORDS.items():
        if any(kw in caption_lower for kw in keywords):
            return tipo
    return "default"


def _get_template(perfil: str, post_type: str) -> str:
    """Retorna template de mensagem por perfil e tipo de post."""
    perfil_clean = perfil.lstrip("@")
    profile_templates = _TEMPLATES.get(perfil_clean, _TEMPLATES["default"])
    return profile_templates.get(post_type, profile_templates["default"])


# ------------------------------------------------------------------
# Sequências de nurturing
# ------------------------------------------------------------------

def _build_sequencia_7dias(perfil: str, post_type: str) -> "ManychatSequencia":
    """Sequência de 7 dias de nurturing."""
    template = _get_template(perfil, post_type)
    mensagens = [
        {"dia": 1, "texto": template},
        {"dia": 2, "texto": "Oi de novo! Só passando para ver se conseguiu as informações. Posso ajudar com mais alguma coisa? {{link}}"},
        {"dia": 3, "texto": "Que tal dar uma olhada nessas dicas extras que separei pra você? {{link}}"},
        {"dia": 4, "texto": "Lembrete amigável: a oferta especial está disponível por tempo limitado! {{link}}"},
        {"dia": 5, "texto": "Curiosidade: você sabia que nossos seguidores têm condições especiais? Confere: {{link}}"},
        {"dia": 6, "texto": "Último dia da semana! Que tal fechar isso hoje? {{link}}"},
        {"dia": 7, "texto": "Obrigado pelo interesse durante a semana! Se quiser mais informações, é só chamar. {{link}}"},
    ]
    return ManychatSequencia(nome="nurturing_7dias", mensagens=mensagens)


def _build_sequencia_30dias(perfil: str, post_type: str) -> "ManychatSequencia":
    """Sequência de 30 dias de nurturing (marcos principais)."""
    template = _get_template(perfil, post_type)
    mensagens = [
        {"dia": 1,  "texto": template},
        {"dia": 3,  "texto": "Oi! Só verificando se conseguiu as informações que precisava. {{link}}"},
        {"dia": 7,  "texto": "1 semana depois — ainda estamos aqui para ajudar! Novidades: {{link}}"},
        {"dia": 10, "texto": "Dica exclusiva para você: {{link}}"},
        {"dia": 14, "texto": "2 semanas! Você é especial para a gente. Confere essa oferta: {{link}}"},
        {"dia": 18, "texto": "Quase 3 semanas de conexão! Conteúdo novo disponível: {{link}}"},
        {"dia": 21, "texto": "3 semanas juntos! Que tal uma conversa sobre seus planos? {{link}}"},
        {"dia": 25, "texto": "Estamos chegando ao fim do mês. Veja o que preparamos: {{link}}"},
        {"dia": 28, "texto": "Últimos dias! Aproveite as condições especiais de fim de mês: {{link}}"},
        {"dia": 30, "texto": "30 dias! Obrigado por nos acompanhar. Sempre que precisar: {{link}}"},
    ]
    return ManychatSequencia(nome="nurturing_30dias", mensagens=mensagens)


# ------------------------------------------------------------------
# Dataclasses
# ------------------------------------------------------------------

@dataclass
class ManychatSequencia:
    nome: str               # "nurturing_7dias" | "nurturing_30dias"
    mensagens: list[dict]   # [{dia: 1, texto: "..."}, ...]

    def to_dict(self) -> dict:
        return {
            "nome": self.nome,
            "total_mensagens": len(self.mensagens),
            "mensagens": self.mensagens,
        }


@dataclass
class ManychatTrigger:
    tipo: str       # "post_comment" | "story_reply"
    keyword: str    # "QUERO" | "LINK" | "INFO"
    post_id: str    # draft_id do post
    account: str    # @perfil
    post_type: str  # hotel | restaurante | praia | default

    def to_dict(self) -> dict:
        return {
            "tipo": self.tipo,
            "keyword": self.keyword,
            "match": "contains",
            "post_id": self.post_id,
            "account": self.account,
            "post_type": self.post_type,
        }


@dataclass
class ManychatPlan:
    plan_id: str
    created_at: str
    perfil: str
    triggers: list[ManychatTrigger]
    sequencias: list[ManychatSequencia]
    total_posts: int
    dry_run: bool
    warnings: list[str]
    plan_path: Path

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "created_at": self.created_at,
            "perfil": self.perfil,
            "total_posts": self.total_posts,
            "dry_run": self.dry_run,
            "warnings": self.warnings,
            "plan_path": str(self.plan_path),
            "triggers": [t.to_dict() for t in self.triggers],
            "sequencias": [s.to_dict() for s in self.sequencias],
            "_note": "ManyChat plan — configure no painel ManyChat com estes dados. NUNCA conectado a API real.",
            "_status": "PLAN — não conectado a API ManyChat real",
        }

    def summary(self) -> str:
        lines = [
            "=== MANYCHAT PLAN ===",
            f"plan_id:     {self.plan_id}",
            f"perfil:      {self.perfil or '(todos)'}",
            f"created_at:  {self.created_at[:19]}",
            f"total_posts: {self.total_posts}",
            f"dry_run:     {self.dry_run}",
            f"triggers:    {len(self.triggers)}",
            f"sequencias:  {len(self.sequencias)}",
        ]
        for t in self.triggers:
            lines.append(f"  [trigger] post={t.post_id} keyword={t.keyword} tipo={t.post_type}")
        for s in self.sequencias:
            lines.append(f"  [seq] {s.nome} — {len(s.mensagens)} mensagens")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  AVISO: {w}")
        lines.append(f"plan_path:   {self.plan_path}")
        return "\n".join(lines)


# ------------------------------------------------------------------
# ManychatPlanner
# ------------------------------------------------------------------

class ManychatPlanner:
    """Gera plano de automação ManyChat a partir de drafts aprovados.

    Uso:
        planner = ManychatPlanner(dry_run=True)
        plan = planner.generate(
            account_filter="oinatalrn",
            keyword="QUERO",
            sequencia="7dias",
        )
        print(plan.summary())

    NUNCA chama API ManyChat real — apenas gera plan.json.
    """

    def __init__(
        self,
        dry_run: bool = True,
        drafts_path: Optional[Path] = None,
        output_base: Path = _DEFAULT_OUT,
        log_path: Optional[Path] = None,
    ) -> None:
        self.dry_run = dry_run
        self.output_base = Path(output_base)
        self._drafts_path = Path(drafts_path) if drafts_path else _ROOT / "data" / "caption_drafts.jsonl"
        self._log_path = Path(log_path) if log_path else _ROOT / "data" / "approval_log.jsonl"

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def generate(
        self,
        account_filter: Optional[str] = None,
        keyword: str = "QUERO",
        sequencia: str = "7dias",
        output_dir: Optional[Path] = None,
        plan_id: Optional[str] = None,
        trigger_type: str = "post_comment",
    ) -> ManychatPlan:
        """Gera o plano ManyChat com triggers e sequências.

        Args:
            account_filter: @perfil para filtrar (None = todos os aprovados)
            keyword:        Palavra-chave que dispara o fluxo (ex: "QUERO")
            sequencia:      "7dias" ou "30dias"
            output_dir:     Pasta de saída (default: data/manychat_plans/<date>-<id>)
            plan_id:        ID do plano (gerado se omitido)
            trigger_type:   "post_comment" | "story_reply"

        Returns:
            ManychatPlan com path do JSON salvo.
        """
        from src.caption_approval.drafts import DraftsManager
        from src.caption_approval.models import DraftStatus

        if plan_id is None:
            plan_id = str(uuid.uuid4())[:8]

        if output_dir is None:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            output_dir = self.output_base / f"{today}-{plan_id}"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Carrega drafts aprovados
        dm = DraftsManager(
            drafts_path=str(self._drafts_path),
            log_path=str(self._log_path),
        )
        all_drafts = [d for d in dm.list_all() if d.status == DraftStatus.APPROVED]

        # Determina perfil dominante e filtra
        perfil_filter = ""
        if account_filter:
            handle = account_filter.lstrip("@")
            all_drafts = [d for d in all_drafts if d.account_handle.lstrip("@") == handle]
            perfil_filter = f"@{handle}"

        warnings: list[str] = []
        if not all_drafts:
            warnings.append("Nenhum draft aprovado encontrado para gerar plano ManyChat")

        # Perfil para templates (usa o filtro ou o primeiro draft)
        perfil_template = perfil_filter or (
            f"@{all_drafts[0].account_handle.lstrip('@')}" if all_drafts else "default"
        )

        # Gera triggers (um por draft aprovado)
        triggers = []
        for draft in all_drafts:
            post_type = _detect_post_type(draft.caption_text)
            triggers.append(ManychatTrigger(
                tipo=trigger_type,
                keyword=keyword,
                post_id=draft.draft_id,
                account=f"@{draft.account_handle.lstrip('@')}",
                post_type=post_type,
            ))

        # Determina o tipo de post dominante para a sequência
        dominant_type = "default"
        if triggers:
            type_counts: dict[str, int] = {}
            for t in triggers:
                type_counts[t.post_type] = type_counts.get(t.post_type, 0) + 1
            dominant_type = max(type_counts, key=lambda k: type_counts[k])

        # Gera sequências
        sequencias: list[ManychatSequencia] = []
        if sequencia == "7dias":
            sequencias.append(_build_sequencia_7dias(perfil_template, dominant_type))
        elif sequencia == "30dias":
            sequencias.append(_build_sequencia_30dias(perfil_template, dominant_type))
        else:
            # sequencia desconhecida: gera 7dias como fallback
            warnings.append(f"Sequência '{sequencia}' desconhecida, usando 7dias como fallback")
            sequencias.append(_build_sequencia_7dias(perfil_template, dominant_type))

        # Salva plan.json SEMPRE (mesmo em dry_run)
        plan_path = output_dir / "plan.json"
        plan = ManychatPlan(
            plan_id=plan_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            perfil=perfil_filter,
            triggers=triggers,
            sequencias=sequencias,
            total_posts=len(triggers),
            dry_run=self.dry_run,
            warnings=warnings,
            plan_path=plan_path,
        )

        plan_path.write_text(
            json.dumps(plan.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        _logger.info(
            "manychat_plan: %s — %d triggers | keyword=%s | seq=%s | dry_run=%s",
            plan_id, len(triggers), keyword, sequencia, self.dry_run,
        )
        return plan
