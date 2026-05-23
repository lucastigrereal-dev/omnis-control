"""ResearchConductor — contrato Protocol para wide research com relatório citado.

STORM (stanford-oval) é a implementação de referência.
A interface é agnóstica de LLM e search backend.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class ResearchSpec:
    """Especificação de uma sessão de wide research."""

    topic: str
    """Tópico ou query principal da pesquisa."""

    max_perspectives: int = 5
    """Máximo de perspectivas/ângulos a explorar (controla amplitude do STORM)."""

    max_search_queries_per_perspective: int = 3
    """Queries de busca por perspectiva."""

    language: str = "pt"
    """Idioma preferido para o relatório final."""

    dry_run: bool = True
    """Se True: retorna plano estruturado sem chamar LLM/search reais."""

    output_dir: str = "output/research/"
    """Diretório para armazenar artefatos (relatório, fontes, citações)."""

    store_in_akasha: bool = False
    """Se True: grava resultado no Akasha (perspectivas + chunks + citações)."""

    extra: dict = field(default_factory=dict)
    """Parâmetros adicionais passados ao backend."""


@dataclass
class ResearchPerspective:
    """Uma perspectiva/ângulo explorado durante a pesquisa."""

    name: str
    questions: list[str] = field(default_factory=list)
    sources_used: list[str] = field(default_factory=list)


@dataclass
class ResearchCitation:
    """Citação de fonte usada no relatório."""

    url: str
    title: str = ""
    snippet: str = ""
    perspective: str = ""


@dataclass
class ResearchResult:
    """Resultado de uma sessão de wide research."""

    success: bool
    topic: str
    report: str
    """Relatório estruturado completo (markdown com seções e citações inline)."""

    perspectives: list[ResearchPerspective] = field(default_factory=list)
    citations: list[ResearchCitation] = field(default_factory=list)
    files_created: list[str] = field(default_factory=list)
    dry_run: bool = True
    error: str | None = None
    artifacts: dict = field(default_factory=dict)

    @property
    def citation_count(self) -> int:
        return len(self.citations)

    @property
    def perspective_count(self) -> int:
        return len(self.perspectives)


@runtime_checkable
class ResearchConductor(Protocol):
    """Contrato Protocol para executores de wide research."""

    def execute(self, spec: ResearchSpec) -> ResearchResult:
        """Executa pesquisa e retorna relatório estruturado com perspectivas e citações."""
        ...

    def health_check(self) -> bool:
        """Retorna True se o backend (LLM + search) está disponível."""
        ...
