"""WeeklyPackOrchestrator — generates a full week of content output as a package."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class WeeklyPackOrchestrator:
    project: str
    niche: str
    objective: str
    city: str
    channel: str
    dry_run: bool = True
    _learning_context: list[str] = field(default_factory=list, repr=False)

    # ------------------------------------------------------------------ #
    # Builder methods
    # ------------------------------------------------------------------ #

    def with_learning_context(self, learnings_path: Path) -> "WeeklyPackOrchestrator":
        """Read a JSONL learnings file and attach learning context to this orchestrator.

        Each line in the JSONL must be a JSON object with a ``"learnings"`` key
        (list[str]).  All learnings from all lines are merged and stored; they are
        injected into generated posts/stories so the pack reflects previous week
        knowledge.

        Returns *self* so it can be chained after construction.
        """
        learnings_path = Path(learnings_path)
        collected: list[str] = []
        for raw_line in learnings_path.read_text(encoding="utf-8").splitlines():
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                obj = json.loads(raw_line)
                collected.extend(obj.get("learnings", []))
            except json.JSONDecodeError:
                pass
        self._learning_context = collected
        return self

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def run(self) -> dict[str, Any]:
        """Generate the full week pack and return a manifest dict."""
        manifest = {
            "project": self.project,
            "niche": self.niche,
            "objective": self.objective,
            "city": self.city,
            "channel": self.channel,
            "dry_run": self.dry_run,
            "generated_at": datetime.utcnow().isoformat(),
            "learning_context": self._learning_context,
            "posts": self._gen_posts(),
            "stories": self._gen_stories(),
            "reels": self._gen_reels(),
            "carousel": self._gen_carousel(),
            "proposal": self._gen_proposal(),
            "learning_update": self._gen_learning_update(),
        }

        self._save_pack(manifest)
        return manifest

    # ------------------------------------------------------------------ #
    # Generators
    # ------------------------------------------------------------------ #

    def _gen_posts(self, n: int = 7) -> list[str]:
        days = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        learning_suffix = ""
        if self._learning_context:
            learning_suffix = f" | learning_context: {self._learning_context[0][:60]}..."
        return [
            f"[DIA {i+1} — {days[i % 7]}] Post {self.niche} em {self.city} | "
            f"Projeto: {self.project} | Canal: {self.channel} | "
            f"Objetivo: {self.objective}{learning_suffix} | "
            f"[dry_run=True — conteúdo template, sem chamada externa]"
            for i in range(n)
        ]

    def _gen_stories(self, n: int = 7) -> list[str]:
        formats = [
            "enquete", "pergunta", "contagem regressiva",
            "link sticker", "quiz", "bastidores", "CTA direto",
        ]
        learning_suffix = ""
        if self._learning_context:
            learning_suffix = f" | learning_context: {self._learning_context[0][:60]}..."
        return [
            f"[STORY {i+1}] Formato: {formats[i % len(formats)]} | "
            f"Niche: {self.niche} | Cidade: {self.city} | "
            f"Projeto: {self.project}{learning_suffix} | [template]"
            for i in range(n)
        ]

    def _gen_reels(self, n: int = 5) -> list[str]:
        hooks = [
            "Você sabia que em {city}...",
            "O segredo de {niche} que ninguém conta",
            "3 dicas de {niche} em {city}",
            "O melhor de {city} em 30 segundos",
            "Por que {objective} muda tudo no {niche}",
        ]
        return [
            f"[REEL {i+1}] Hook: {hooks[i % len(hooks)].format(city=self.city, niche=self.niche, objective=self.objective)} | "
            f"Roteiro: intro → desenvolvimento → CTA → follow | "
            f"Projeto: {self.project} | [template]"
            for i in range(n)
        ]

    def _gen_carousel(self) -> dict[str, Any]:
        return {
            "title": f"Top 5 de {self.niche} em {self.city}",
            "slides": [
                f"Slide {i+1}: dica {i+1} de {self.niche} — {self.city} | [template]"
                for i in range(5)
            ],
            "cta": f"Salva esse carrossel e compartilha! | Projeto: {self.project}",
            "project": self.project,
        }

    def _gen_proposal(self) -> dict[str, Any]:
        return {
            "title": f"Proposta Comercial — {self.project}",
            "niche": self.niche,
            "channel": self.channel,
            "city": self.city,
            "objective": self.objective,
            "packages": [
                {"name": "Starter", "price": "R$350", "items": ["1 collab", "1 perfil", "1 post"]},
                {"name": "Growth", "price": "R$990/mês", "items": ["3 collabs", "3 páginas", "SEOgram"]},
                {"name": "Premium", "price": "R$1.200", "items": ["4 collabs", "3 stories", "3+ perfis"]},
            ],
            "note": "[template — sem chamada externa]",
        }

    def _gen_learning_update(self) -> dict[str, Any]:
        return {
            "summary": f"Semana de produção {self.niche} em {self.city} — projeto {self.project}",
            "learnings": [
                f"Aprendizado 1: melhor horário para {self.niche} no {self.channel}",
                f"Aprendizado 2: formato que mais engaja em {self.city}",
                f"Aprendizado 3: hook mais eficaz para objetivo '{self.objective}'",
            ],
            "next_actions": [
                f"Gravar reels semana seguinte",
                f"Revisar métricas de engajamento",
                f"Atualizar proposta comercial para {self.city}",
            ],
            "note": "[template]",
        }

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #

    def _mission_dir(self) -> Path:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        base = Path("missions") / f"{self.project}_weekly_{date_str}"
        base.mkdir(parents=True, exist_ok=True)
        return base

    def _save_pack(self, manifest: dict[str, Any]) -> None:
        d = self._mission_dir()

        (d / "weekly_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        (d / "posts.md").write_text(
            "# Posts da Semana\n\n" + "\n\n".join(f"## Post {i+1}\n{p}" for i, p in enumerate(manifest["posts"])),
            encoding="utf-8",
        )

        (d / "stories.md").write_text(
            "# Stories da Semana\n\n" + "\n\n".join(f"## Story {i+1}\n{s}" for i, s in enumerate(manifest["stories"])),
            encoding="utf-8",
        )

        (d / "reels.md").write_text(
            "# Reels da Semana\n\n" + "\n\n".join(f"## Reel {i+1}\n{r}" for i, r in enumerate(manifest["reels"])),
            encoding="utf-8",
        )

        carousel = manifest["carousel"]
        carousel_md = f"# Carrossel\n\n**Título:** {carousel['title']}\n\n"
        carousel_md += "\n".join(f"- {s}" for s in carousel["slides"])
        carousel_md += f"\n\n**CTA:** {carousel['cta']}\n"
        (d / "carousel.md").write_text(carousel_md, encoding="utf-8")

        proposal = manifest["proposal"]
        proposal_md = f"# {proposal['title']}\n\n"
        for pkg in proposal["packages"]:
            proposal_md += f"## {pkg['name']} — {pkg['price']}\n"
            proposal_md += "\n".join(f"- {item}" for item in pkg["items"]) + "\n\n"
        (d / "proposal.md").write_text(proposal_md, encoding="utf-8")

        lu = manifest["learning_update"]
        lu_md = f"# Learning Update\n\n**Resumo:** {lu['summary']}\n\n## Aprendizados\n"
        lu_md += "\n".join(f"- {l}" for l in lu["learnings"])
        lu_md += "\n\n## Próximas Ações\n"
        lu_md += "\n".join(f"- {a}" for a in lu["next_actions"])
        (d / "learning_update.md").write_text(lu_md, encoding="utf-8")
