"""Template Library — Modelos de legenda por objetivo.

Templates são usados como ponto de partida para criar rascunhos.
Organizados por objetivo primeiro (alcance, autoridade, conversao, relacionamento, teste)
e opcionalmente por formato (reels, carousel, stories, feed).
"""

import json
import os
from pathlib import Path

from .models import CaptionTemplate

TEMPLATES_PATH = os.path.expanduser("~/omnis-control/data/caption_templates.json")


def _default_templates() -> list[CaptionTemplate]:
    """Templates padrão incluídos no sistema."""
    return [
        # ---- Alcance ----
        CaptionTemplate(
            template_id="alcance_reels",
            name="Alcance — Reels",
            objective="alcance",
            format="reels",
            hook_template="[HOOK A REVISAR] — você precisa ver isso!",
            body_template="[CORPO DA LEGENDA A REVISAR]\n\n📍 [LOCAL]",
            cta_template="Salva pra ver depois e compartilha com alguém que precisa saber disso! 💬",
            hashtag_suggestions=["#viagem", "#turismo", "#brasil"],
            notes="Reels de alcance: hook forte nos primeiros 3 segundos",
        ),
        CaptionTemplate(
            template_id="alcance_carousel",
            name="Alcance — Carrossel",
            objective="alcance",
            format="carousel",
            hook_template="[HOOK A REVISAR] — desliza pro lado!",
            body_template="[CORPO DA LEGENDA A REVISAR]\n\n📍 [LOCAL]",
            cta_template="Compartilha com alguém que precisa ver isso! Salva pra consultar depois.",
            hashtag_suggestions=["#viagem", "#turismo", "#brasil"],
            notes="Carrossel de alcance: primeira foto/chamada forte",
        ),
        # ---- Autoridade ----
        CaptionTemplate(
            template_id="autoridade_feed",
            name="Autoridade — Feed",
            objective="autoridade",
            format=None,
            hook_template="[HOOK A REVISAR] — aqui está o que aprendi:",
            body_template="[CORPO DA LEGENDA A REVISAR]\n\n📍 [LOCAL]",
            cta_template="O que você acha disso? Conta aqui nos comentários! 👇",
            hashtag_suggestions=["#marketing", "#crescimento", "#estrategia"],
            notes="Conteúdo de autoridade: dados, aprendizados, cases",
        ),
        # ---- Conversão ----
        CaptionTemplate(
            template_id="conversao_feed",
            name="Conversão — Feed",
            objective="conversao",
            format=None,
            hook_template="[HOOK A REVISAR] — e a melhor parte:",
            body_template="[CORPO DA LEGENDA A REVISAR]\n\n📍 [LOCAL]\n\n👉 [NOME_DO_HOTEL]",
            cta_template="Garanta seu desconto exclusivo no link da bio! 🔗",
            hashtag_suggestions=["#resort", "#hospedagem", "#viagem"],
            notes="Foco em conversão: desconto, oferta, CTA direto",
        ),
        # ---- Relacionamento ----
        CaptionTemplate(
            template_id="relacionamento_stories",
            name="Relacionamento — Stories/Feed",
            objective="relacionamento",
            format=None,
            hook_template="[HOOK A REVISAR] — me conta nos comentários:",
            body_template="[CORPO DA LEGENDA A REVISAR]\n\n📍 [LOCAL]",
            cta_template="Responde aqui: o que você faria no meu lugar? 👇",
            hashtag_suggestions=["#familia", "#momento", "#reflexao"],
            notes="Engajamento: perguntas, enquetes, opinião",
        ),
        # ---- Teste ----
        CaptionTemplate(
            template_id="teste_flex",
            name="Teste — Formato livre",
            objective="teste",
            format=None,
            hook_template="[HOOK A REVISAR] — teste:",
            body_template="[CORPO DA LEGENDA A REVISAR]",
            cta_template="Me diz: funcionou pra você? Comenta aqui!",
            hashtag_suggestions=["#teste", "#novidade", "#experiencia"],
            notes="Teste: novo formato, novo nicho, novo approach",
        ),
    ]


class TemplateLibrary:
    """Gerencia templates de legenda."""

    def __init__(self, path: str = TEMPLATES_PATH):
        self.path = path
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        """Cria arquivo com templates padrão se não existir."""
        if not os.path.isfile(self.path):
            Path(os.path.dirname(self.path)).mkdir(parents=True, exist_ok=True)
            templates = _default_templates()
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump([t.to_dict() for t in templates], f, indent=2, ensure_ascii=False)

    def list_all(self) -> list[CaptionTemplate]:
        """Lista todos os templates disponíveis."""
        if not os.path.isfile(self.path):
            return _default_templates()
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        return [CaptionTemplate.from_dict(t) for t in data]

    def get_by_objective(self, objective: str) -> list[CaptionTemplate]:
        """Retorna templates para um objetivo."""
        return [t for t in self.list_all() if t.objective == objective]

    def get_by_format(self, format: str) -> list[CaptionTemplate]:
        """Retorna templates para um formato."""
        return [t for t in self.list_all() if t.format is None or t.format == format]

    def get_best_match(self, objective: str, format: str) -> CaptionTemplate | None:
        """Melhor template: match objetivo + formato, fallback para objetivo."""
        # Match exato
        for t in self.list_all():
            if t.objective == objective and (t.format is None or t.format == format):
                return t
        # Match objetivo só
        for t in self.list_all():
            if t.objective == objective:
                return t
        return None

    def render(
        self,
        template: CaptionTemplate,
        hook: str = "",
        body: str = "",
        cta: str = "",
        local: str = "",
        hotel: str = "",
    ) -> dict[str, object]:
        """Renderiza um template substituindo placeholders."""
        hook_text = hook if hook else template.hook_template
        body_text = body if body else template.body_template
        cta_text = cta if cta else template.cta_template

        # Substituir placeholders comuns
        if local:
            body_text = body_text.replace("[LOCAL]", local)
        if hotel:
            body_text = body_text.replace("[NOME_DO_HOTEL]", hotel)

        # Montar caption_text
        hashtags = " ".join(f"#{h}" for h in (template.hashtag_suggestions or []))
        caption_text = f"{hook_text}\n\n{body_text}\n\n{cta_text}"
        if hashtags:
            caption_text += f"\n\n{hashtags}"

        return {
            "caption_text": caption_text,
            "cta": cta_text,
            "hashtags": template.hashtag_suggestions[:],
        }
