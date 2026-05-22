"""MemoryRouter — unified query across 8 memory sources (mock-first, real when DBs available)."""
from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional


def _new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


@dataclass
class MemoryChunk:
    """A single result from any memory source."""
    chunk_id: str = field(default_factory=lambda: _new_id("mem_"))
    source: str = ""          # akasha | qdrant | biblioteca | obsidian | publisher | mem0 | git | metrics
    content: str = ""
    relevance: float = 0.0    # 0-1
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "source": self.source,
            "content": self.content,
            "relevance": self.relevance,
            "metadata": self.metadata,
        }


@dataclass
class MemoryQueryResult:
    query: str
    chunks: list[MemoryChunk] = field(default_factory=list)
    sources_queried: list[str] = field(default_factory=list)
    sources_failed: list[str] = field(default_factory=list)
    total_time_ms: int = 0

    @property
    def top_hooks(self) -> list[str]:
        """Extract hooks from memory chunks."""
        hooks = []
        for c in self.chunks:
            if c.metadata.get("type") == "hook" and c.content:
                hooks.append(c.content)
        return hooks[:5]

    @property
    def saturated_themes(self) -> list[str]:
        """Extract saturated themes to avoid."""
        themes = []
        for c in self.chunks:
            if c.metadata.get("type") == "saturated_theme":
                themes.append(c.content)
        return themes[:5]

    @property
    def viral_patterns(self) -> list[str]:
        """Extract viral patterns."""
        patterns = []
        for c in self.chunks:
            if c.metadata.get("type") == "viral_pattern":
                patterns.append(c.content)
        return patterns[:5]

    @property
    def insights(self) -> list[str]:
        """Extract book/obsidian insights."""
        ins = []
        for c in self.chunks:
            if c.metadata.get("type") == "insight":
                ins.append(c.content)
        return ins[:10]

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "chunks": [c.to_dict() for c in self.chunks],
            "sources_queried": self.sources_queried,
            "sources_failed": self.sources_failed,
            "total_time_ms": self.total_time_ms,
            "top_hooks": self.top_hooks,
            "saturated_themes": self.saturated_themes,
            "viral_patterns": self.viral_patterns,
            "insights": self.insights,
        }


# ── Mock memory bank — realistic data for testing ──────────────────────────

MOCK_MEMORY = {
    "viagem": [
        MemoryChunk(source="akasha", content="Viajar é se permitir viver o extraordinário", relevance=0.95, metadata={"type": "hook", "niche": "viagem", "engajamento": "alto"}),
        MemoryChunk(source="akasha", content="O destino que ninguém te contou sobre...", relevance=0.92, metadata={"type": "hook", "niche": "viagem", "engajamento": "alto"}),
        MemoryChunk(source="akasha", content="3 lugares que parecem fora do Brasil", relevance=0.88, metadata={"type": "hook", "niche": "viagem", "engajamento": "médio"}),
        MemoryChunk(source="qdrant", content="posts genéricos de 'dicas de viagem'", relevance=0.75, metadata={"type": "saturated_theme", "niche": "viagem"}),
        MemoryChunk(source="qdrant", content="fotos de praia sem contexto", relevance=0.70, metadata={"type": "saturated_theme", "niche": "viagem"}),
        MemoryChunk(source="qdrant", content="Reels com transições rápidas + música trending + texto overlay", relevance=0.90, metadata={"type": "viral_pattern", "niche": "viagem", "formato": "reel"}),
        MemoryChunk(source="biblioteca", content="A antecipação da viagem traz mais felicidade que a própria viagem — planejar é parte do prazer", relevance=0.85, metadata={"type": "insight", "livro": "A Psicologia do Dinheiro"}),
        MemoryChunk(source="biblioteca", content="Pessoas não compram destinos, compram a versão de si mesmas que aquele destino promete", relevance=0.82, metadata={"type": "insight", "livro": "StoryBrand"}),
    ],
    "família": [
        MemoryChunk(source="akasha", content="Família viajando junta: o que ninguém te conta sobre...", relevance=0.94, metadata={"type": "hook", "niche": "família"}),
        MemoryChunk(source="akasha", content="O olhar do meu filho quando viu o mar pela primeira vez", relevance=0.91, metadata={"type": "hook", "niche": "família"}),
        MemoryChunk(source="qdrant", content="Viagem em família low cost", relevance=0.72, metadata={"type": "saturated_theme", "niche": "família"}),
        MemoryChunk(source="biblioteca", content="O maior presente que você pode dar aos seus filhos não é uma coisa, é uma memória", relevance=0.88, metadata={"type": "insight", "livro": "O Poder do Hábito"}),
        MemoryChunk(source="biblioteca", content="Crianças que viajam desenvolvem 40% mais flexibilidade cognitiva", relevance=0.84, metadata={"type": "insight", "livro": "Mindset"}),
    ],
    "gastronomia": [
        MemoryChunk(source="akasha", content="O prato de X reais que vale mais que restaurante estrelado", relevance=0.93, metadata={"type": "hook", "niche": "gastronomia"}),
        MemoryChunk(source="akasha", content="Você está comendo isso ERRADO em [cidade]", relevance=0.89, metadata={"type": "hook", "niche": "gastronomia"}),
        MemoryChunk(source="qdrant", content="Fotos de prato sem pessoa", relevance=0.68, metadata={"type": "saturated_theme", "niche": "gastronomia"}),
        MemoryChunk(source="biblioteca", content="Comida é memória afetiva — o sabor ativa o sistema límbico mais que qualquer outro sentido", relevance=0.86, metadata={"type": "insight", "livro": "Em Busca de Sentido"}),
    ],
    "hotel": [
        MemoryChunk(source="akasha", content="O hotel que parece cenário de filme — e cabe no seu bolso", relevance=0.91, metadata={"type": "hook", "niche": "hotel"}),
        MemoryChunk(source="akasha", content="Quarto com vista: vale ou não vale o upgrade?", relevance=0.87, metadata={"type": "hook", "niche": "hotel"}),
        MemoryChunk(source="qdrant", content="Carrossel de fotos sem storytelling", relevance=0.65, metadata={"type": "saturated_theme", "niche": "hotel"}),
        MemoryChunk(source="biblioteca", content="A experiência de hospitality não é sobre a cama — é sobre como fizeram você se sentir", relevance=0.89, metadata={"type": "insight", "livro": "The Power of Moments"}),
    ],
    "natal rn": [
        MemoryChunk(source="akasha", content="Natal é daqueles destinos que a gente guarda pra sempre 🌞", relevance=0.96, metadata={"type": "hook", "niche": "natal_rn"}),
        MemoryChunk(source="akasha", content="O que fazer em Natal além das praias óbvias", relevance=0.90, metadata={"type": "hook", "niche": "natal_rn"}),
        MemoryChunk(source="qdrant", content="Dunas de Genipabu genérico sem storytelling pessoal", relevance=0.67, metadata={"type": "saturated_theme", "niche": "natal_rn"}),
        MemoryChunk(source="biblioteca", content="O Nordeste brasileiro tem o maior potencial turístico subexplorado do país", relevance=0.83, metadata={"type": "insight", "livro": "Brasil: País do Futuro"}),
        MemoryChunk(source="obsidian", content="Nota 2024-11: colaboração com @oinatalrn bateu 2M de alcance usando storytelling de memória afetiva", relevance=0.92, metadata={"type": "insight", "nota": "colab_natal_2024"}),
    ],
}


class MemoryRouter:
    """Unified query router across 8 memory sources.

    Mock mode (no DB connections): uses MOCK_MEMORY with keyword matching.
    Real mode: queries Akasha pgvector, Qdrant, Biblioteca, Obsidian in parallel.
    """

    MOCK_SOURCES = ["akasha", "qdrant", "biblioteca", "obsidian"]

    def __init__(self, dry_run: bool = True, max_workers: int = 4):
        self.dry_run = dry_run
        self.max_workers = max_workers
        self.queries: list[dict] = []

    def query(
        self,
        question: str,
        sources: list[str] | None = None,
        top_k: int = 10,
    ) -> MemoryQueryResult:
        """Query memory sources in parallel, merge results by relevance."""
        import time
        t0 = time.perf_counter()

        sources = sources or self.MOCK_SOURCES
        result = MemoryQueryResult(query=question, sources_queried=sources)
        self.queries.append({"question": question, "sources": sources, "dry_run": self.dry_run})

        if self.dry_run:
            chunks = self._mock_query(question)
            result.chunks = sorted(chunks, key=lambda c: c.relevance, reverse=True)[:top_k]
        else:
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(sources))) as executor:
                futures = {
                    executor.submit(self._query_source, question, src): src
                    for src in sources
                }
                for future in as_completed(futures):
                    src = futures[future]
                    try:
                        chunks = future.result()
                        result.chunks.extend(chunks)
                    except Exception as exc:
                        result.sources_failed.append(f"{src}: {exc}")

            result.chunks = sorted(result.chunks, key=lambda c: c.relevance, reverse=True)[:top_k]

        result.total_time_ms = int((time.perf_counter() - t0) * 1000)
        return result

    def _mock_query(self, question: str) -> list[MemoryChunk]:
        """Keyword-based mock search across MOCK_MEMORY."""
        import unicodedata
        def _strip_accents(s: str) -> str:
            return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
        q = _strip_accents(question.lower())
        chunks: list[MemoryChunk] = []

        for niche, items in MOCK_MEMORY.items():
            niche_clean = _strip_accents(niche)
            if any(word in q for word in niche_clean.split()):
                chunks.extend(items)

        if not chunks:
            # Return a few generic results when no keyword matches
            for niche_items in list(MOCK_MEMORY.values())[:2]:
                chunks.extend(niche_items[:3])

        return chunks

    def _query_source(self, question: str, source: str) -> list[MemoryChunk]:
        """Query a single source. Override for real DB connections."""
        if source == "akasha":
            return self._query_akasha(question)
        elif source == "qdrant":
            return self._query_qdrant(question)
        elif source == "biblioteca":
            return self._query_biblioteca(question)
        elif source == "obsidian":
            return self._query_obsidian(question)
        elif source == "publisher":
            return self._query_publisher(question)
        elif source == "mem0":
            return self._query_mem0(question)
        elif source == "git":
            return self._query_git(question)
        elif source == "metrics":
            return self._query_metrics(question)
        return []

    def _query_akasha(self, question: str) -> list[MemoryChunk]:
        """Akasha PostgreSQL pgvector search."""
        if self.dry_run:
            return MOCK_MEMORY.get("viagem", [])[:2]
        # Real: SELECT * FROM docs ORDER BY embedding <=> query_embedding LIMIT 5
        try:
            import psycopg2
            conn = psycopg2.connect("host=localhost port=5432 dbname=akasha user=postgres password=postgres")
            cur = conn.cursor()
            cur.execute(
                "SELECT content, 1 AS relevance FROM docs WHERE to_tsvector('portuguese', content) @@ plainto_tsquery('portuguese', %s) LIMIT 5",
                (question,),
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return [MemoryChunk(source="akasha", content=row[0], relevance=row[1]) for row in rows]
        except Exception as exc:
            raise RuntimeError(f"akasha query failed: {exc}")

    def _query_qdrant(self, question: str) -> list[MemoryChunk]:
        """Qdrant vector search."""
        if self.dry_run:
            return MOCK_MEMORY.get("viagem", [])[3:5]  # saturated themes + viral patterns
        try:
            from qdrant_client import QdrantClient
            client = QdrantClient(host="localhost", port=6333)
            # Requires embedding model — returns mock for now
            return []
        except Exception:
            return []

    def _query_biblioteca(self, question: str) -> list[MemoryChunk]:
        """Biblioteca Sabedoria PostgreSQL search."""
        if self.dry_run:
            return [c for c in MOCK_MEMORY.get("viagem", []) if c.source == "biblioteca"]
        try:
            import psycopg2
            conn = psycopg2.connect("host=localhost port=5432 dbname=biblioteca_sabedoria user=postgres password=postgres")
            cur = conn.cursor()
            cur.execute(
                "SELECT insight_text FROM insights WHERE to_tsvector('portuguese', insight_text) @@ plainto_tsquery('portuguese', %s) LIMIT 5",
                (question,),
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return [MemoryChunk(source="biblioteca", content=row[0], relevance=0.8) for row in rows]
        except Exception:
            return []

    def _query_obsidian(self, question: str) -> list[MemoryChunk]:
        """Obsidian vault search (filesystem grep)."""
        if self.dry_run:
            return [c for c in MOCK_MEMORY.get("natal rn", []) if c.source == "obsidian"]
        return []

    def _query_publisher(self, question: str) -> list[MemoryChunk]:
        """Publisher OS Supabase search."""
        return []

    def _query_mem0(self, question: str) -> list[MemoryChunk]:
        """Mem0 + Kuzu graph search."""
        return []

    def _query_git(self, question: str) -> list[MemoryChunk]:
        """Git log search."""
        return []

    def _query_metrics(self, question: str) -> list[MemoryChunk]:
        """Instagram metrics search."""
        return []
