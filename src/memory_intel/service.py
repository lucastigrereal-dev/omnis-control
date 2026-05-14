"""P21 Memory Intelligence service — contextual retrieval and writeback engine."""
from __future__ import annotations

from typing import Optional

from src.memory_intel.models import (
    MemoryIntelConfig,
    MemoryIntelMode,
    RetrievalResult,
    PatternResult,
    INTENT_TO_SOURCES,
    VALID_INTENTS,
    MAX_ASSEMBLED_TEXT_CHARS,
    MAX_SNIPPET_CHARS,
    MAX_HITS_PER_SOURCE,
    MAX_RECORDS_PER_MISSION,
    _new_id,
    _now_iso,
)
from src.memory_intel.errors import (
    MemoryIntelError,
    RetrievalError,
    WritebackError,
    ContextTooLargeError,
    NoSourcesAvailableError,
    SafetyViolationError,
)
from src.memory_pack.models import (
    ContextPack,
    MemoryQuery,
    MemoryHit,
    MissionMemoryRecord,
    MemoryWritePlan,
    MemorySource,
    SOURCE_AKASHA,
    SOURCE_SESSION,
    SOURCE_OBSIDIAN,
    VALID_SOURCES,
    VALID_SECTORS,
    RELEVANCE_LOW,
    RELEVANCE_MEDIUM,
    RELEVANCE_HIGH,
    RELEVANCE_EXACT,
    RELEVANCE_NONE,
    RELEVANCE_RANK,
    STATUS_DRAFT,
    STATUS_ACTIVE,
    STATUS_SUPERSEDED,
    ACTION_UPSERT,
)
from src.memory_pack.service import MemoryPackPlanner


# ── Main Service ─────────────────────────────────────────────────────────────

class MemoryIntelligence:
    """Motor de inteligencia contextual.

    Uso:
        mi = MemoryIntelligence(dry_run=True)

        # Pre-missao
        context = mi.retrieve(intent="create_campaign", sector="midia",
                              mission_id="spr_abc123")

        # Pos-missao
        plan = mi.writeback(mission, report)
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.planner = MemoryPackPlanner.create()
        self.config = MemoryIntelConfig.load()

    # ── Retrieval ─────────────────────────────────────────────────────────

    def retrieve(
        self,
        intent: str,
        sector: str,
        mission_id: str,
        max_hits: int | None = None,
        tags: list[str] | None = None,
    ) -> RetrievalResult:
        """Recupera contexto completo para uma missao.

        Args:
            intent: Tipo de missao (create_campaign, publish_content, etc.)
            sector: Setor JARVIS (midia, comercial, etc.)
            mission_id: ID da missao Supreme
            max_hits: Maximo de hits (default: config.max_hits)
            tags: Tags para filtro adicional

        Returns:
            RetrievalResult com ContextPack + missoes similares + padroes
        """
        warnings: list[str] = []
        max_hits = max_hits or self.config.max_hits

        # Step 1: Source selection
        sources = self._select_sources(intent)
        if not sources:
            raise NoSourcesAvailableError(
                f"Nenhuma fonte disponivel para intent={intent!r}"
            )

        # Step 2: Build query
        query_text = self._build_query_text(intent, sector, tags)

        try:
            query = MemoryQuery.new(
                text=query_text,
                sources=sources,
                sectors=[sector] if sector in VALID_SECTORS else [],
                max_hits=max_hits,
                min_relevance=RELEVANCE_LOW,
            )
        except ValueError as e:
            raise RetrievalError(f"Falha ao construir query: {e}") from e

        # Step 3: Simulated retrieval
        try:
            sim_result = self.planner.simulate_query(query)
        except Exception as e:
            raise RetrievalError(f"Falha na simulacao de query: {e}") from e

        hits: list[MemoryHit] = sim_result.get("hits", [])

        # Step 4: Rank & filter (already done by simulate_query, but ensure limits)
        hits = self._enforce_source_limits(hits)

        # Step 5: Assemble ContextPack
        pack = ContextPack.new(query_id=query.query_id)
        if hits:
            pack.assemble(hits)
        pack = self._optimize_pack(pack)

        # Step 6: Similar missions
        similar = self.retrieve_similar_missions(intent, sector, tags)

        # Step 7: Extract patterns
        patterns = self.extract_patterns(sector, intent)

        return RetrievalResult.new(
            query_id=query.query_id,
            pack=pack,
            similar_missions=similar,
            patterns=patterns.to_dict(),
            dry_run=self.dry_run,
            warnings=warnings,
        )

    def retrieve_context(
        self,
        intent: str,
        sector: str,
        max_hits: int | None = None,
    ) -> ContextPack:
        """Recupera apenas o ContextPack (sem similares nem padroes).

        Args:
            intent: Tipo de missao
            sector: Setor JARVIS
            max_hits: Maximo de hits

        Returns:
            ContextPack populado
        """
        max_hits = max_hits or self.config.max_hits
        sources = self._select_sources(intent)
        query_text = self._build_query_text(intent, sector)

        query = MemoryQuery.new(
            text=query_text,
            sources=sources,
            sectors=[sector] if sector in VALID_SECTORS else [],
            max_hits=max_hits,
            min_relevance=RELEVANCE_LOW,
        )

        sim_result = self.planner.simulate_query(query)
        hits: list[MemoryHit] = sim_result.get("hits", [])
        hits = self._enforce_source_limits(hits)

        pack = ContextPack.new(query_id=query.query_id)
        if hits:
            pack.assemble(hits)
        return self._optimize_pack(pack)

    def retrieve_similar_missions(
        self,
        intent: str,
        sector: str,
        tags: list[str] | None = None,
        limit: int | None = None,
    ) -> list:
        """Encontra missoes anteriores similares.

        Args:
            intent: Tipo de missao
            sector: Setor JARVIS
            tags: Tags para matching
            limit: Maximo de resultados

        Returns:
            Lista de MissionSimilarityResult
        """
        from src.memory_intel.similarity import find_similar_missions

        limit = limit or self.config.max_similar_results

        past_records = self._get_past_records(sector)

        if not past_records:
            return []

        return find_similar_missions(
            intent=intent,
            sector=sector,
            tags=tags or [],
            past_records=past_records,
            limit=limit,
        )

    def extract_patterns(self, sector: str, intent: str) -> PatternResult:
        """Extrai padroes de sucesso/fracasso para sector+intent.

        Args:
            sector: Setor JARVIS
            intent: Tipo de missao

        Returns:
            PatternResult com hooks, modulos, falhas, insights
        """
        records = self._get_past_records(sector)

        if not records:
            return PatternResult.new(sector=sector, intent=intent, sample_count=0)

        successful_hooks: list[str] = []
        common_modules: set[str] = set()
        failure_patterns: list[str] = []
        all_insights: list[str] = []

        for record in records:
            if record.status == STATUS_SUPERSEDED:
                continue

            for outcome in record.outcomes:
                if "success" in outcome.lower() or "success_rate" in outcome.lower():
                    successful_hooks.append(record.title)

            for insight in record.key_insights:
                all_insights.append(insight)

            for tag in record.tags:
                if tag == "failure":
                    failure_patterns.append(record.summary)

            if record.metadata:
                for key in record.metadata:
                    if key.startswith("module_"):
                        common_modules.add(record.metadata[key])

        # Dedup insights (max 5)
        unique_insights = list(dict.fromkeys(all_insights))[:5]

        # Dedup failures (max 5)
        unique_failures = list(dict.fromkeys(failure_patterns))[:5]

        # Dedup hooks (max 5)
        unique_hooks = list(dict.fromkeys(successful_hooks))[:5]

        return PatternResult.new(
            sector=sector,
            intent=intent,
            successful_hooks=unique_hooks,
            common_modules=sorted(common_modules),
            failure_patterns=unique_failures,
            insights=unique_insights,
            sample_count=len(records),
        )

    # ── Writeback ─────────────────────────────────────────────────────────

    def writeback(self, mission, report) -> MemoryWritePlan:
        """Persiste aprendizados de uma missao completa.

        Args:
            mission: SupremeMission (aceita dict ou objeto com to_dict())
            report: MissionReport (aceita dict ou objeto com to_dict())

        Returns:
            MemoryWritePlan com registros gerados e aprovacao pendente
        """
        records = self._extract_learnings(report)
        if not records:
            return MemoryWritePlan.new(
                target_source=SOURCE_AKASHA,
                action=ACTION_UPSERT,
                notes="Writeback: zero aprendizados extraidos da missao",
            )

        plan = self.planner.plan_memory_writeback(
            records=records,
            target_source=SOURCE_AKASHA,
            action=ACTION_UPSERT,
            notes=f"Writeback plan para missao {getattr(mission, 'mission_id', mission.get('mission_id', 'unknown'))}",
        )

        # Validate safety
        self._validate_writeback_safety(plan)

        return plan

    def learn_from_step(
        self,
        mission_id: str,
        step: dict,
        result: dict,
    ) -> MissionMemoryRecord | None:
        """Aprende com um step individual.

        Args:
            mission_id: ID da missao
            step: Dados do SupremeStep (dict)
            result: Resultado da execucao do step (dict)

        Returns:
            MissionMemoryRecord ou None se nada a aprender
        """
        step_id = step.get("step_id", "unknown")
        operation = step.get("operation", "unknown")
        status = result.get("status", "unknown")

        sector = step.get("sector", "produto")
        if sector not in VALID_SECTORS:
            sector = "produto"

        if status == "failed":
            return MissionMemoryRecord.new(
                mission_id=mission_id,
                sector=sector,
                title=f"Falha: {operation}",
                summary=f"Step {step_id} falhou: {result.get('error', 'unknown')}",
                key_insights=[f"Evitar {operation} sem validar pre-requisitos"],
                decisions=[f"Nao repetir {operation} nestas condicoes"],
                outcomes=["step_failed"],
                tags=["failure", str(step.get("module_ref", "unknown"))],
            )

        if status == "done":
            return MissionMemoryRecord.new(
                mission_id=mission_id,
                sector=sector,
                title=f"Sucesso: {operation}",
                summary=f"Step concluido em {result.get('duration_ms', '?')}ms",
                key_insights=[f"Pipeline {step.get('module_ref', 'unknown')} funcionou"],
                outcomes=[f"duration_ms={result.get('duration_ms', 0)}"],
                tags=["success", str(step.get("module_ref", "unknown"))],
            )

        return None

    # ── Internals ─────────────────────────────────────────────────────────

    def _select_sources(self, intent: str) -> list[str]:
        """Seleciona fontes com base no intent.

        Args:
            intent: Tipo de missao

        Returns:
            Lista de nomes de fontes validas
        """
        if intent in INTENT_TO_SOURCES:
            return list(INTENT_TO_SOURCES[intent])
        if intent in VALID_INTENTS:
            return list(self.config.intent_to_sources.get(intent, [SOURCE_AKASHA, SOURCE_SESSION]))
        return [SOURCE_AKASHA, SOURCE_SESSION]

    def _build_query_text(
        self,
        intent: str,
        sector: str,
        tags: list[str] | None = None,
    ) -> str:
        """Monta texto de query a partir de intent + sector + tags.

        Args:
            intent: Tipo de missao
            sector: Setor JARVIS
            tags: Tags adicionais

        Returns:
            Texto formatado para query
        """
        parts = [intent.replace("_", " "), sector.replace("_", " ")]
        if tags:
            parts.extend(tags)
        return " ".join(parts)

    def _optimize_pack(self, pack: ContextPack) -> ContextPack:
        """Otimiza ContextPack: limita tamanho, trunca snippets.

        Args:
            pack: ContextPack a otimizar

        Returns:
            ContextPack otimizado (modificado in-place)
        """
        # Truncate snippets
        for hit in pack.hits:
            if len(hit.snippet) > self.config.max_snippet_chars:
                hit.snippet = hit.snippet[: self.config.max_snippet_chars - 3] + "..."

        # Check assembled_text size
        if len(pack.assembled_text) > self.config.max_assembled_chars:
            # Remove lowest relevance hits until it fits
            sorted_hits = sorted(pack.hits, key=lambda h: h.rank_score, reverse=True)
            trimmed = []
            for hit in sorted_hits:
                trimmed.append(hit)
                test_pack = ContextPack.new(query_id=pack.query_id)
                test_pack.assemble(trimmed)
                if len(test_pack.assembled_text) > self.config.max_assembled_chars and len(trimmed) > 1:
                    trimmed.pop()
                    break

            if trimmed:
                pack.assemble(trimmed)

        return pack

    def _enforce_source_limits(self, hits: list[MemoryHit]) -> list[MemoryHit]:
        """Garante maximo de hits por fonte.

        Args:
            hits: Lista de MemoryHit

        Returns:
            Lista filtrada
        """
        source_counts: dict[str, int] = {}
        result = []
        for hit in hits:
            count = source_counts.get(hit.source_type, 0)
            if count < self.config.max_hits_per_source:
                result.append(hit)
                source_counts[hit.source_type] = count + 1
        return result

    def _extract_learnings(self, report) -> list[MissionMemoryRecord]:
        """Extrai aprendizados de um MissionReport.

        Args:
            report: MissionReport (dict ou objeto)

        Returns:
            Lista de MissionMemoryRecord (max 5)
        """
        report_dict = report if isinstance(report, dict) else report.to_dict()
        records: list[MissionMemoryRecord] = []
        mission_id = report_dict.get("mission_id", "unknown")

        steps = report_dict.get("steps_summary", [])

        # Learn from failed steps
        for step in steps:
            if step.get("status") == "failed":
                operation = step.get("operation", "unknown")
                sector = step.get("sector", "produto")
                if sector not in VALID_SECTORS:
                    sector = "produto"
                records.append(
                    MissionMemoryRecord.new(
                        mission_id=mission_id,
                        sector=sector,
                        title=f"Falha: {operation}",
                        summary=f"Step {step.get('step_id', '?')} falhou: {step.get('error', 'unknown')}",
                        key_insights=[
                            f"Evitar {operation} sem {step.get('missing_dep', 'pre-requisito')}"
                        ],
                        decisions=[f"Nao repetir {operation} nestas condicoes"],
                        outcomes=["step_failed"],
                        tags=["failure", str(step.get("module_ref", "unknown"))],
                    )
                )

        # Learn from successful steps
        for step in steps:
            if step.get("status") == "done":
                operation = step.get("operation", "unknown")
                sector = step.get("sector", "produto")
                if sector not in VALID_SECTORS:
                    sector = "produto"
                records.append(
                    MissionMemoryRecord.new(
                        mission_id=mission_id,
                        sector=sector,
                        title=f"Sucesso: {operation}",
                        summary=f"Step concluido em {step.get('duration_ms', '?')}ms",
                        key_insights=[
                            f"Pipeline {step.get('module_ref', 'unknown')} funcionou para {mission_id}"
                        ],
                        outcomes=[f"duration_ms={step.get('duration_ms', 0)}"],
                        tags=["success", str(step.get("module_ref", "unknown"))],
                    )
                )

        # Metric summary
        metrics = report_dict.get("metrics", {})
        if metrics:
            total_steps = metrics.get("total_steps", 0)
            success_rate = metrics.get("success_rate", 0)
            records.append(
                MissionMemoryRecord.new(
                    mission_id=mission_id,
                    sector="produto",
                    title=f"Metricas: {mission_id}",
                    summary=f"Missao envolveu {total_steps} steps, {success_rate}% sucesso",
                    key_insights=metrics.get("insights", []),
                    outcomes=[f"success_rate={success_rate}%"],
                    tags=["metrics", "summary"],
                )
            )

        # Enforce max records per mission
        return records[: self.config.max_records_per_mission]

    def _validate_writeback_safety(self, plan: MemoryWritePlan) -> None:
        """Valida regras de seguranca no write plan.

        Args:
            plan: MemoryWritePlan a validar

        Raises:
            SafetyViolationError: Se alguma regra for violada
        """
        if not plan.is_dry_run:
            raise SafetyViolationError(
                "Write plan deve ter is_dry_run=True. Operacoes reais bloqueadas."
            )
        if not plan.requires_approval:
            raise SafetyViolationError(
                "Write plan deve ter requires_approval=True."
            )
        if plan.action == "delete":
            raise SafetyViolationError(
                "Acao DELETE bloqueada por padrao em writeback."
            )
        if plan.record_count > self.config.max_records_per_mission:
            raise SafetyViolationError(
                f"Write plan excede max_records_per_mission ({self.config.max_records_per_mission}): "
                f"{plan.record_count} records"
            )

    def _get_past_records(self, sector: str) -> list[MissionMemoryRecord]:
        """Obtem registros passados simulados para um setor.

        Args:
            sector: Setor JARVIS

        Returns:
            Lista de MissionMemoryRecord simulados
        """
        if sector not in VALID_SECTORS:
            return []

        # Generate deterministic simulated records based on sector
        simulated = {
            "midia": [
                MissionMemoryRecord.new(
                    mission_id="spr_past_001",
                    sector="midia",
                    title="Campanha Hotel Natal 2026 — aprendizados",
                    summary="Campanha gerou 3 collabs, ROI 4.2x",
                    key_insights=["Hotels respondem melhor quarta-feira", "Carrossel > Reels para hotel"],
                    decisions=["Precificar Growth a R$990"],
                    outcomes=["success_rate=100%", "3 collabs fechadas"],
                    tags=["success", "campaign", "hotel"],
                    metadata={"intent": "create_campaign"},
                ),
                MissionMemoryRecord.new(
                    mission_id="spr_past_002",
                    sector="midia",
                    title="Falha: publish em horario errado",
                    summary="Post publicado 23h teve 80% menos engagement",
                    key_insights=["Publicar entre 9h-11h ou 18h-20h"],
                    decisions=["Nao publicar apos 22h"],
                    outcomes=["step_failed"],
                    tags=["failure", "publish", "timing"],
                    metadata={"intent": "publish_content"},
                ),
            ],
            "comercial": [
                MissionMemoryRecord.new(
                    mission_id="spr_past_003",
                    sector="comercial",
                    title="SDR Hotels — 150 leads Interior SP",
                    summary="Pipeline manual gerou 12 respostas em 48h",
                    key_insights=["DM direta funciona melhor que comment", "Personalizar com nome do hotel"],
                    decisions=["Focar em hoteis com perfil ativo no Instagram"],
                    outcomes=["success_rate=80%", "12 respostas"],
                    tags=["success", "sdr", "outreach"],
                    metadata={"intent": "commercial_outreach"},
                ),
            ],
        }

        return simulated.get(sector, [])
