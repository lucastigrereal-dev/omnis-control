"""CaptionDraftAgent — agente mínimo real que executa o loop completo.

Loop: QueueItem → MemoryContext → CaptionDraft (texto gerado) → AgentRun salvo.
Dry-run por padrão: nenhuma escrita permanente, nenhuma chamada LLM externa.
"""
from __future__ import annotations

import uuid

from src.agentic.agent_models import AgentRun, AgentRunRepository, AgentRunStatus
from src.caption_approval.drafts import DraftsManager
from src.caption_approval.models import DraftStatus
from src.content_queue.queue import Queue
from src.memory.interface import MemoryInterface


# ── geração de texto (sem LLM) ───────────────────────────────────────────────

_HOOK_BY_OBJECTIVE: dict[str, str] = {
    "alcance": "Você precisa conhecer esse lugar",
    "conversao": "Reservas abertas — mas por tempo limitado",
    "autoridade": "Depois de visitar dezenas de destinos, posso dizer:",
    "relacionamento": "Esse momento ficou guardado na memória",
}

_HASHTAGS_BY_ACCOUNT: dict[str, list[str]] = {
    "oinatalrn": ["#natal", "#turismorn", "#visitenatal", "#riogrande", "#rnturismo"],
    "agenteviajabrasil": ["#viajebrasil", "#brasil", "#destinosbrasil", "#turismo"],
    "oquecomernatalrn": ["#gastronomia", "#natal", "#restaurante", "#comida", "#foodrn"],
    "afamiliatigrereal": ["#familia", "#viagem", "#viajandocomfilhos", "#ferias"],
    "lucastigrereal": ["#lifestyle", "#viagem", "#tigrereal", "#dicas"],
    "natalaivoueu": ["#natal", "#praias", "#nordeste", "#viagem", "#rn"],
}


def _build_caption(objective: str, account_handle: str, context_md: str) -> str:
    hook = _HOOK_BY_OBJECTIVE.get(objective, "Descubra isso com a gente")
    handle = account_handle.lstrip("@").lower()
    body_hint = "• Detalhes únicos do local\n• Experiência real\n• Por que vale a pena"
    cta = "Salva esse post e manda para quem vai adorar saber!"
    return f"{hook}\n\n{body_hint}\n\n{cta}"


def _pick_hashtags(account_handle: str) -> list[str]:
    handle = account_handle.lstrip("@").lower()
    return _HASHTAGS_BY_ACCOUNT.get(handle, ["#viagem", "#brasil", "#turismo"])[:5]


# ── agente ───────────────────────────────────────────────────────────────────


class CaptionDraftAgent:
    """Agente que transforma um QueueItem em um CaptionDraft."""

    def __init__(
        self,
        dry_run: bool = True,
        queue: Queue | None = None,
        drafts_manager: DraftsManager | None = None,
        memory: MemoryInterface | None = None,
        repo: AgentRunRepository | None = None,
    ) -> None:
        self.dry_run = dry_run
        self._queue = queue or Queue()
        self._drafts = drafts_manager or DraftsManager()
        self._memory = memory or MemoryInterface(dry_run=dry_run)
        self._repo = repo or AgentRunRepository()

    def run(self, queue_id: str) -> AgentRun:
        """Executa o loop completo para um item da fila."""
        run = AgentRun(
            run_id=uuid.uuid4().hex[:12],
            agent="caption_draft_agent",
            account_handle="",
            objective="",
            dry_run=self.dry_run,
        )

        # ── Step 1: fetch queue item ──────────────────────────────────────────
        step1 = run.add_step("fetch_queue_item", input_summary=f"queue_id={queue_id}")
        item = self._queue.get(queue_id)
        if not item:
            step1.fail(f"QueueItem não encontrado: {queue_id}")
            run.fail(f"QueueItem não encontrado: {queue_id}")
            self._repo.save(run)
            return run

        run.account_handle = item.account_handle
        run.objective = item.objective or "alcance"
        step1.complete(
            f"account={item.account_handle} objective={run.objective} format={item.format}"
        )

        # ── Step 2: query memory ──────────────────────────────────────────────
        step2 = run.add_step(
            "query_memory",
            input_summary=f"account={item.account_handle} intent={run.objective}",
        )
        mission_id = f"AGT-{run.run_id}"
        mem_ctx = self._memory.query(
            mission_id=mission_id,
            account_handle=item.account_handle,
            intent=run.objective,
        )
        step2.complete(
            f"patterns={mem_ctx.patterns} similar={len(mem_ctx.similar_captions)}"
        )

        # ── Step 3: generate caption text ─────────────────────────────────────
        step3 = run.add_step("generate_caption", input_summary=f"objective={run.objective}")
        caption_text = _build_caption(run.objective, item.account_handle, mem_ctx.context_markdown)
        hashtags = _pick_hashtags(item.account_handle)
        step3.complete(f"len={len(caption_text)} hashtags={len(hashtags)}")

        # ── Step 4: create draft ──────────────────────────────────────────────
        step4 = run.add_step("create_draft", input_summary=f"dry_run={self.dry_run}")
        if self.dry_run:
            draft_id = f"dry-{uuid.uuid4().hex[:8]}"
            step4.complete(f"draft_id={draft_id} [dry_run — não persistido]")
        else:
            draft = self._drafts.create(
                queue_id=queue_id,
                account_handle=item.account_handle,
                caption_text=caption_text,
                hashtags=hashtags,
                objective=run.objective,
                format=item.format or "feed",
            )
            draft_id = draft.draft_id
            step4.complete(f"draft_id={draft_id} status={DraftStatus.DRAFT}")

        run.complete(result={
            "draft_id": draft_id,
            "caption_len": len(caption_text),
            "hashtags": hashtags,
            "memory_patterns": mem_ctx.patterns,
            "dry_run": self.dry_run,
        })
        self._repo.save(run)
        return run
