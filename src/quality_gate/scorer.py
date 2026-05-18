"""Quality Scorer — evaluates outputs on multiple dimensions."""

from __future__ import annotations

import re
from typing import Optional

from .models import QualityReport, ScoredDimension


class QualityScorer:
    """Score output quality across standard dimensions."""

    # Dimension weights by output type
    WEIGHTS = {
        "caption": {"clarity": 2.0, "hook_strength": 2.5, "seo": 1.5, "cta": 1.5, "tone": 1.0, "risk": 1.5},
        "carrossel": {"clarity": 2.0, "visual_structure": 2.0, "hook_strength": 2.0, "seo": 1.0, "cta": 1.5, "risk": 1.5},
        "reel": {"clarity": 1.5, "hook_strength": 3.0, "seo": 1.0, "cta": 1.5, "tone": 1.0, "risk": 2.0},
        "dm": {"clarity": 2.0, "personalization": 2.5, "cta": 2.0, "tone": 1.5, "risk": 2.0},
        "app": {"clarity": 2.0, "structure": 2.0, "tests": 2.0, "completeness": 2.0, "risk": 2.0},
    }

    HOOK_PATTERNS = [
        (r"voc[eê]\s+(precisa|deveria|tem que)", 8.0),
        (r"descubra|conhe[cç]a|veja", 7.0),
        (r"segredo|nunca\s+\w+|ningu[eé]m\s+\w+", 8.5),
        (r"(melhor|pior|top)\s+\d+", 7.5),
        (r"aten[cç][aã]o|cuidado|pare", 6.0),
        (r"\?$", 6.5),
    ]

    DANGEROUS_PATTERNS = [
        (r"garantimos?\s+(resultado|lucro|venda)", "promessa de resultado garantido"),
        (r"\d+%\s+(garantido|certeza)", "porcentagem sem fonte"),
        (r"gr[aá]tis|gratuito|sem custo", "promessa gratuita — verificar legalidade"),
        (r"compre\s+(agora|j[aá]|hoje)", "pressao excessiva de compra"),
        (r"pre[cç]o\s+imperd[ií]vel|[uú]ltima\s+chance", "urgencia artificial"),
    ]

    WEAK_WORDS = {"talvez", "acho", "poderia", "quem sabe", "vamos ver", "quem dera"}

    def score(self, output_id: str, output_type: str, content: str, metadata: Optional[dict] = None) -> QualityReport:
        """Score content quality and generate report."""
        metadata = metadata or {}
        weights = self.WEIGHTS.get(output_type, self.WEIGHTS["caption"])

        report = QualityReport(output_id=output_id, output_type=output_type)

        dimensions = []

        if "clarity" in weights:
            dimensions.append(self._score_clarity(content, weights["clarity"]))

        if "hook_strength" in weights:
            dimensions.append(self._score_hook(content, weights["hook_strength"]))

        if "seo" in weights:
            dimensions.append(self._score_seo(content, weights["seo"]))

        if "cta" in weights:
            dimensions.append(self._score_cta(content, weights["cta"]))

        if "tone" in weights:
            dimensions.append(self._score_tone(content, weights["tone"]))

        if "risk" in weights:
            dimensions.append(self._score_risk(content, weights["risk"]))

        if "visual_structure" in weights:
            dimensions.append(self._score_visual_structure(content, weights["visual_structure"]))

        if "structure" in weights:
            dimensions.append(self._score_structure(content, weights["structure"]))

        if "tests" in weights:
            dimensions.append(self._score_tests(content, weights["tests"]))

        if "completeness" in weights:
            dimensions.append(self._score_completeness(content, weights["completeness"]))

        if "personalization" in weights:
            dimensions.append(self._score_personalization(content, metadata, weights["personalization"]))

        report.dimensions = dimensions

        # Calculate overall
        total_weight = sum(d.weight for d in dimensions)
        if total_weight > 0:
            report.overall_score = sum(d.weighted_score for d in dimensions) / total_weight

        report.grade = self._grade(report.overall_score)
        report.ready_for_use = report.overall_score >= 7.0 and report.failed_dimensions == 0

        if report.ready_for_use:
            report.recommendation = "Pronto para uso. Publicar com confianca."
        elif report.overall_score >= 6.0:
            report.recommendation = "Revisar antes de publicar. Dimensoes fracas precisam de atencao."
        else:
            report.recommendation = "Refazer. Qualidade abaixo do minimo aceitavel."

        return report

    # ---- Dimension scorers ----

    def _score_clarity(self, content: str, weight: float) -> ScoredDimension:
        issues = []
        words = len(content.split())
        sentences = len(re.findall(r'[.!?]+', content))

        score = 7.0
        if words < 50:
            score -= 2
            issues.append("Conteudo muito curto (< 50 palavras)")
        if sentences > 0:
            avg_words = words / sentences
            if avg_words > 35:
                score -= 1
                issues.append("Frases muito longas (> 35 palavras por frase)")

        weak_found = [w for w in self.WEAK_WORDS if w in content.lower()]
        if weak_found:
            score -= len(weak_found) * 0.5
            issues.append(f"Palavras fracas: {', '.join(weak_found)}")

        return ScoredDimension(
            name="clarity", score=max(0, min(10, score)), weight=weight,
            verdict="OK" if score >= 7 else "REVISAR", issues=issues,
        )

    def _score_hook(self, content: str, weight: float) -> ScoredDimension:
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        if not lines:
            return ScoredDimension(name="hook_strength", score=0, weight=weight, verdict="FALHA", issues=["Sem conteudo"])

        first_line = lines[0]
        score = 3.0
        for pattern, hook_score in self.HOOK_PATTERNS:
            if re.search(pattern, first_line, re.IGNORECASE):
                score = hook_score
                break

        suggestions = []
        if score < 6:
            suggestions = [
                "Use hook com pergunta ou curiosidade na primeira linha",
                "Comece com 'Voce sabia...' ou 'Descubra...'",
            ]

        return ScoredDimension(
            name="hook_strength", score=score, weight=weight,
            verdict="FORTE" if score >= 7 else ("MEDIO" if score >= 5 else "FRACO"),
            suggestions=suggestions,
        )

    def _score_seo(self, content: str, weight: float) -> ScoredDimension:
        hashtags = re.findall(r'#\w+', content)
        keywords = len(re.findall(r'\b(praia|hotel|resort|viagem|turismo|gastronomia|familia|natal|nordeste|brasil)\b', content.lower()))

        score = 5.0 + min(3, len(hashtags)) + min(2, keywords)
        issues = []
        if len(hashtags) < 3:
            issues.append("Poucas hashtags (< 3)")
        if keywords < 2:
            issues.append("Poucas keywords de nicho")

        return ScoredDimension(
            name="seo", score=min(10, score), weight=weight,
            verdict="OTIMIZADO" if score >= 7 else "MELHORAR",
            issues=issues,
            suggestions=["Incluir 5-10 hashtags relevantes", "Usar keywords do nicho naturalmente"],
        )

    def _score_cta(self, content: str, weight: float) -> ScoredDimension:
        cta_patterns = [
            r"comenta?\s+(aqui|aí|o que|qual)",
            r"salva?\s+(para|pra)",
            r"compartilha?\s+(com|para)",
            r"link\s+(na|do)\s+(bio|perfil|story)",
            r"arrasta?\s+(pra|para)\s+(cima|lado)",
        ]

        found = sum(1 for p in cta_patterns if re.search(p, content, re.IGNORECASE))
        score = min(10, found * 3.0 + 3.0)

        return ScoredDimension(
            name="cta", score=score, weight=weight,
            verdict="FORTE" if found >= 2 else ("MEDIO" if found == 1 else "AUSENTE"),
            suggestions=[] if found >= 2 else ["Adicionar CTA: salvar, comentar, compartilhar"],
        )

    def _score_tone(self, content: str, weight: float) -> ScoredDimension:
        personal = len(re.findall(r'\b(eu|meu|minha|fui|fiz|aprendi|descobri|amo|gosto|fiquei|fomos|comi|provei|curti|amei)\b', content.lower()))
        score = 5.0 + min(5, personal * 0.5)

        return ScoredDimension(
            name="tone", score=min(10, score), weight=weight,
            verdict="PESSOAL" if personal >= 4 else "GENERICO",
            suggestions=[] if personal >= 4 else ["Usar mais linguagem pessoal: 'eu fiz', 'descobri'"],
        )

    def _score_risk(self, content: str, weight: float) -> ScoredDimension:
        issues = []
        for pattern, desc in self.DANGEROUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(desc)

        score = 10.0 - len(issues) * 3.0

        return ScoredDimension(
            name="risk", score=max(0, score), weight=weight,
            verdict="SEGURO" if not issues else "ATENCAO",
            issues=issues,
            suggestions=["Remover promessas nao comprovaveis", "Evitar urgencia artificial"],
        )

    def _score_visual_structure(self, content: str, weight: float) -> ScoredDimension:
        slides = content.count("---") + content.count("Slide") + content.count("slide")
        score = 5.0 + min(5, slides)
        return ScoredDimension(
            name="visual_structure", score=min(10, score), weight=weight,
            verdict="BEM_ESTRUTURADO" if slides >= 5 else "POUCOS_SLIDES",
            suggestions=[] if slides >= 5 else ["Carrossel precisa de pelo menos 5 slides"],
        )

    def _score_structure(self, content: str, weight: float) -> ScoredDimension:
        has_imports = "import " in content or "from " in content
        has_classes = "class " in content
        has_functions = "def " in content
        score = 3.0 + (2 if has_imports else 0) + (3 if has_classes else 0) + (2 if has_functions else 0)
        return ScoredDimension(name="structure", score=score, weight=weight, verdict="OK" if score >= 7 else "INCOMPLETO")

    def _score_tests(self, content: str, weight: float) -> ScoredDimension:
        test_count = content.count("def test_")
        score = min(10, test_count * 2.0 + 2.0)
        return ScoredDimension(
            name="tests", score=score, weight=weight,
            verdict="COBERTO" if test_count >= 3 else "POUCOS_TESTES",
            suggestions=[] if test_count >= 3 else ["Adicionar pelo menos 3 testes unitarios"],
        )

    def _score_completeness(self, content: str, weight: float) -> ScoredDimension:
        markers = ["README", "requirements", "main.py", "models.py", "database", "tests/"]
        found = sum(1 for m in markers if m.lower() in content.lower())
        score = 3.0 + found * 1.5
        return ScoredDimension(name="completeness", score=min(10, score), weight=weight,
                               verdict="COMPLETO" if found >= 4 else "INCOMPLETO")

    def _score_personalization(self, content: str, metadata: dict, weight: float) -> ScoredDimension:
        name_used = metadata.get("recipient_name", "") in content if metadata.get("recipient_name") else False
        company_used = metadata.get("company_name", "") in content if metadata.get("company_name") else False
        score = 4.0 + (3 if name_used else 0) + (3 if company_used else 0)
        return ScoredDimension(
            name="personalization", score=score, weight=weight,
            verdict="PERSONALIZADO" if score >= 8 else "GENERICO",
            suggestions=[] if score >= 8 else ["Usar nome do destinatario", "Mencionar empresa/projeto"],
        )

    def _grade(self, score: float) -> str:
        if score >= 9.0:
            return "A"
        elif score >= 7.5:
            return "B"
        elif score >= 6.0:
            return "C"
        elif score >= 4.0:
            return "D"
        return "F"
