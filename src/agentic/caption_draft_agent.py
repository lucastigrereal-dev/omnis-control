"""CaptionDraftAgent — agente mínimo real que executa o loop completo.

Loop: QueueItem → Memory → LLM → Draft → Gate → caption_ready → MemoryWriteback.
dry_run=True por padrão: usa MockLLMAdapter, sem persistência permanente.
"""
from __future__ import annotations

import uuid

from src.agentic.agent_models import AgentRun, AgentRunRepository, AgentStep
from src.agentic.llm_adapter import (
    CaptionPromptInput,
    LiteLLMAdapter,
    LLMAdapter,
    MockLLMAdapter,
)
from src.caption_approval.approvals import ApprovalGate
from src.caption_approval.drafts import DraftsManager
from src.caption_approval.models import DraftStatus
from src.content_queue.models import QueueItem, QueueStatus
from src.content_queue.queue import Queue
from src.memory.caption_memory import CaptionMemoryWriter
from src.memory.interface import MemoryContext, MemoryInterface


class CaptionDraftAgent:
    """Agente que transforma um QueueItem em um CaptionDraft via LLM."""

    def __init__(
        self,
        dry_run: bool = True,
        queue: Queue | None = None,
        drafts_manager: DraftsManager | None = None,
        memory: MemoryInterface | None = None,
        repo: AgentRunRepository | None = None,
        llm: LLMAdapter | None = None,
        memory_writer: CaptionMemoryWriter | None = None,
    ) -> None:
        self.dry_run = dry_run
        self._queue = queue or Queue()
        self._drafts = drafts_manager or DraftsManager()
        self._memory = memory or MemoryInterface(dry_run=dry_run)
        self._repo = repo or AgentRunRepository()
        self._llm: LLMAdapter = llm or (MockLLMAdapter() if dry_run else LiteLLMAdapter())
        self._memory_writer = memory_writer or CaptionMemoryWriter()

    # ── public ───────────────────────────────────────────────────────────────

    def run(self, queue_id: str) -> AgentRun:
        """Executa o loop completo para um item da fila."""
        run = AgentRun(
            run_id=uuid.uuid4().hex[:12],
            agent="caption_draft_agent",
            account_handle="",
            objective="",
            dry_run=self.dry_run,
        )

        item = self._fetch_queue_item(run, queue_id)
        if item is None:
            self._repo.save(run)
            return run

        mem_ctx = self._query_memory(run, item)
        llm_output = self._generate_caption(run, item, mem_ctx)
        if run.status == "failed":
            self._repo.save(run)
            return run

        draft_id = self._persist_draft(run, item, llm_output)
        gate_result = self._run_approval_gate(run, draft_id, item)
        self._write_memory(run, item, llm_output, gate_result, draft_id)

        run.complete(result={
            "draft_id": draft_id,
            "caption_len": len(llm_output.raw),
            "hashtags": llm_output.hashtags,
            "model_used": llm_output.model_used,
            "tokens_used": llm_output.tokens_used,
            "memory_patterns": mem_ctx.patterns,
            "gate_verdict": gate_result["verdict"],
            "gate_blocks": gate_result["blocks"],
            "queue_status": gate_result["queue_status"],
            "memory_written": gate_result.get("memory_written", False),
            "dry_run": self.dry_run,
        })
        self._repo.save(run)
        return run

    # ── private steps ─────────────────────────────────────────────────────────

    def _fetch_queue_item(self, run: AgentRun, queue_id: str) -> QueueItem | None:
        step = run.add_step("fetch_queue_item", input_summary=f"queue_id={queue_id}")
        item = self._queue.get(queue_id)
        if not item:
            step.fail(f"QueueItem não encontrado: {queue_id}")
            run.fail(f"QueueItem não encontrado: {queue_id}")
            return None
        run.account_handle = item.account_handle
        run.objective = item.objective or "alcance"
        step.complete(
            f"account={item.account_handle} objective={run.objective} format={item.format}"
        )
        return item

    def _query_memory(self, run: AgentRun, item: QueueItem) -> MemoryContext:
        step = run.add_step(
            "query_memory",
            input_summary=f"account={item.account_handle} intent={run.objective}",
        )
        mem_ctx = self._memory.query(
            mission_id=f"AGT-{run.run_id}",
            account_handle=item.account_handle,
            intent=run.objective,
        )
        step.complete(
            f"patterns={mem_ctx.patterns} similar={len(mem_ctx.similar_captions)}"
        )
        return mem_ctx

    def _generate_caption(
        self, run: AgentRun, item: QueueItem, mem_ctx: MemoryContext
    ) -> "CaptionLLMOutput":  # noqa: F821
        from src.agentic.llm_adapter import CaptionLLMOutput  # local import avoids circular

        step = run.add_step(
            "generate_caption",
            input_summary=f"objective={run.objective} model={self._llm.__class__.__name__}",
        )
        prompt = CaptionPromptInput(
            account_handle=item.account_handle,
            objective=run.objective,
            format=item.format or "feed",
            context_md=mem_ctx.context_markdown,
            similar_captions=mem_ctx.similar_captions,
        )
        try:
            output = self._llm.generate_caption(prompt)
            step.complete(
                f"len={len(output.raw)} hashtags={len(output.hashtags)} model={output.model_used}"
            )
            return output
        except Exception as exc:
            step.fail(str(exc))
            run.fail(f"Geração de legenda falhou: {exc}")
            # retorna output vazio para encerrar o run sem crash
            return CaptionLLMOutput(
                hook="", body="", cta="", hashtags=[], raw="",
                model_used="error", tokens_used=0,
            )

    def _persist_draft(
        self, run: AgentRun, item: QueueItem, llm_output: "CaptionLLMOutput"  # noqa: F821
    ) -> str:
        step = run.add_step("create_draft", input_summary=f"dry_run={self.dry_run}")
        if self.dry_run:
            draft_id = f"dry-{uuid.uuid4().hex[:8]}"
            step.complete(f"draft_id={draft_id} [dry_run — não persistido]")
            return draft_id

        draft = self._drafts.create(
            queue_id=item.queue_id,
            account_handle=item.account_handle,
            caption_text=llm_output.raw,
            hashtags=llm_output.hashtags,
            cta=llm_output.cta,
            objective=run.objective,
            format=item.format or "feed",
        )
        step.complete(f"draft_id={draft.draft_id} status={DraftStatus.DRAFT}")
        return draft.draft_id

    def _run_approval_gate(
        self, run: AgentRun, draft_id: str, item: QueueItem
    ) -> dict[str, object]:
        step = run.add_step(
            "approval_gate",
            input_summary=f"draft_id={draft_id} dry_run={self.dry_run}",
        )

        if self.dry_run:
            step.complete("dry_run — gate simulado: approved")
            return {"verdict": "approved_dry", "blocks": [], "queue_status": "caption_ready"}

        gate = ApprovalGate(drafts_manager=self._drafts)
        draft = self._drafts.get(draft_id)
        if not draft:
            step.fail(f"Draft {draft_id} não encontrado para gate")
            return {"verdict": "error", "blocks": ["draft not found"], "queue_status": "unchanged"}

        # submete para revisão
        self._drafts.submit(draft_id)

        # valida
        validation = gate.validate(
            caption_text=draft.caption_text,
            hashtags=draft.hashtags,
            cta=draft.cta,
        )

        if validation.blocked:
            step.complete(
                f"verdict=needs_review blocks={len(validation.blocks)}"
            )
            return {
                "verdict": "needs_review",
                "blocks": validation.blocks,
                "queue_status": "unchanged",
            }

        # auto-aprova e atualiza queue
        def _queue_updater(queue_id: str, status: str) -> bool:
            result = self._queue.update(queue_id, status=status)
            return result is not None

        try:
            gate.approve(draft_id, queue_updater=_queue_updater)
            step.complete("verdict=approved queue=caption_ready")
            return {"verdict": "approved", "blocks": [], "queue_status": QueueStatus.CAPTION_READY}
        except ValueError as exc:
            step.complete(f"verdict=needs_review reason={exc}")
            return {"verdict": "needs_review", "blocks": [str(exc)], "queue_status": "unchanged"}

    def _write_memory(
        self,
        run: AgentRun,
        item: QueueItem,
        llm_output: "CaptionLLMOutput",  # noqa: F821
        gate_result: dict[str, object],
        draft_id: str,
    ) -> None:
        verdict = gate_result.get("verdict", "")
        approved = verdict in ("approved", "approved_dry")

        step = run.add_step(
            "memory_writeback",
            input_summary=f"approved={approved} dry_run={self.dry_run}",
        )

        if not approved:
            step.skip("não aprovado — sem writeback")
            gate_result["memory_written"] = False
            return

        if self.dry_run:
            step.complete("dry_run — writeback simulado")
            gate_result["memory_written"] = False
            return

        try:
            self._memory_writer.write(
                account_handle=item.account_handle,
                objective=run.objective,
                format=item.format or "feed",
                caption_text=llm_output.raw,
                run_id=run.run_id,
                draft_id=draft_id,
            )
            step.complete(f"gravado account={item.account_handle} objective={run.objective}")
            gate_result["memory_written"] = True
        except Exception as exc:
            step.fail(str(exc))
            gate_result["memory_written"] = False
