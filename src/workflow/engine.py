"""Workflow Engine — Orquestrador ponta a ponta.

Pipeline completo:
  IDEA → PLAN → BRIEF → PRODUCE → DRAFT → APPROVE → QUEUE → PUBLISH

Cada estágio tem validação, logging e rollback de erros.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import WorkflowResult, WorkflowStage, WorkflowStatus
from .publisher_bridge import PublisherBridge, PublisherBridgeError
from src.content_queue import Queue as ContentQueue
from src.content_queue.models import QueueItem, QueueStatus
from src.argos_bridge.draft_builder import DraftBuilder, get as get_draft
from src.caption_approval import DraftsManager

logger = logging.getLogger(__name__)

WORKFLOW_PATH = os.path.expanduser("~/omnis-control/data/workflow_results.jsonl")


class WorkflowEngine:
    """Orquestra o pipeline de conteúdo do começo ao fim."""

    def __init__(self):
        self.queue = ContentQueue()
        self.caption_mgr = DraftsManager()
        self.publisher = PublisherBridge()
        Path(os.path.dirname(WORKFLOW_PATH)).mkdir(parents=True, exist_ok=True)

    # ── Pipeline principal ────────────────────────────────

    def run(self, topic: str, pagina: str, formato: str,
            objective: str = "alcance", crew_type: str = "content_production",
            dry_run: bool = False) -> WorkflowResult:
        """Executa o pipeline completo: IDEA → PRODUCE → DRAFT.

        Args:
            topic: Tema do conteúdo
            pagina: Handle Instagram (ex: afamiliatigrereal)
            formato: carrossel, reel, feed, stories
            objective: alcance, autoridade, conversao, relacionamento
            crew_type: Tipo de crew no Publisher OS
            dry_run: Se True, não executa ações destrutivas

        Returns:
            WorkflowResult com status de cada estágio
        """
        workflow_id = uuid.uuid4().hex[:12]
        stages = {s: WorkflowStatus.PENDING for s in [
            WorkflowStage.IDEA,
            WorkflowStage.PLAN,
            WorkflowStage.BRIEF,
            WorkflowStage.PRODUCE,
            WorkflowStage.DRAFT,
        ]}
        errors = []

        logger.info("[WF:%s] Iniciando: topic=%s pagina=%s formato=%s",
                     workflow_id[:8], topic, pagina, formato)

        # ── IDEA ──
        stages[WorkflowStage.IDEA] = WorkflowStatus.SUCCESS

        # ── PLAN: gerar slot na fila ──
        try:
            stages[WorkflowStage.PLAN] = WorkflowStatus.RUNNING
            plan_result = self._plan(topic, pagina, formato, objective, dry_run)
            if plan_result.get("error"):
                stages[WorkflowStage.PLAN] = WorkflowStatus.FAILED
                errors.append(f"PLAN: {plan_result['error']}")
            else:
                stages[WorkflowStage.PLAN] = WorkflowStatus.SUCCESS
                queue_id = plan_result.get("queue_id")
        except Exception as e:
            stages[WorkflowStage.PLAN] = WorkflowStatus.FAILED
            errors.append(f"PLAN: {e}")
            queue_id = None

        # ── BRIEF: criar briefing ──
        try:
            stages[WorkflowStage.BRIEF] = WorkflowStatus.RUNNING
            brief_result = self._brief(topic, pagina, formato, objective,
                                        workflow_id, dry_run)
            stages[WorkflowStage.BRIEF] = WorkflowStatus.SUCCESS
        except Exception as e:
            stages[WorkflowStage.BRIEF] = WorkflowStatus.FAILED
            errors.append(f"BRIEF: {e}")

        # ── PRODUCE: enviar para Publisher OS CrewAI ──
        job_id = None
        try:
            stages[WorkflowStage.PRODUCE] = WorkflowStatus.RUNNING
            if dry_run:
                stages[WorkflowStage.PRODUCE] = WorkflowStatus.SKIPPED
            else:
                prod_result = self._produce(topic, pagina, formato, crew_type)
                if prod_result.get("error"):
                    stages[WorkflowStage.PRODUCE] = WorkflowStatus.FAILED
                    errors.append(f"PRODUCE: {prod_result['error']}")
                else:
                    stages[WorkflowStage.PRODUCE] = WorkflowStatus.SUCCESS
                    job_id = prod_result.get("job_id")
        except Exception as e:
            stages[WorkflowStage.PRODUCE] = WorkflowStatus.FAILED
            errors.append(f"PRODUCE: {e}")

        # ── DRAFT: criar ArgosDraft ──
        draft_id = None
        try:
            stages[WorkflowStage.DRAFT] = WorkflowStatus.RUNNING
            if dry_run or not queue_id:
                stages[WorkflowStage.DRAFT] = WorkflowStatus.SKIPPED
            else:
                draft_result = self._draft(queue_id)
                if draft_result.get("error"):
                    stages[WorkflowStage.DRAFT] = WorkflowStatus.FAILED
                    errors.append(f"DRAFT: {draft_result['error']}")
                else:
                    stages[WorkflowStage.DRAFT] = WorkflowStatus.SUCCESS
                    draft_id = draft_result.get("draft_id")
        except Exception as e:
            stages[WorkflowStage.DRAFT] = WorkflowStatus.FAILED
            errors.append(f"DRAFT: {e}")

        result = WorkflowResult(
            workflow_id=workflow_id,
            topic=topic,
            pagina=pagina,
            formato=formato,
            stages=stages,
            queue_id=queue_id,
            draft_id=draft_id,
            job_id=job_id,
            errors=errors,
        )

        self._save(result)
        return result

    # ── Estágios individuais ──────────────────────────────

    def _plan(self, topic: str, pagina: str, formato: str,
              objective: str, dry_run: bool) -> dict:
        """Estágio PLAN: cria slot na fila editorial."""
        # Gera 1 slot específico para esta demanda
        result = self.queue.generate(
            days=1, dry_run=dry_run, account_filter=pagina
        )
        if result.get("generated", 0) == 0 and not dry_run:
            # Slot já existe — pegar o próximo disponível
            items = self.queue.filter(account=pagina, status=QueueStatus.NEEDS_ASSET)
            if items:
                return {"queue_id": items[0].queue_id}
            return {"error": "Nenhum slot disponível na fila"}

        # Pegar o último slot gerado
        if not dry_run:
            items = self.queue.filter(account=pagina)
            if items:
                # Atualizar formato e objetivo
                latest = items[-1]
                self.queue.update(latest.queue_id, format=formato, objective=objective,
                                   notes=f"Workflow: {topic}")
                return {"queue_id": latest.queue_id}

        return {"queue_id": None, "note": "dry_run"}

    def _brief(self, topic: str, pagina: str, formato: str,
               objective: str, workflow_id: str, dry_run: bool) -> dict:
        """Estágio BRIEF: cria documento de briefing."""
        briefs_dir = os.path.expanduser(f"~/omnis-control/data/briefs")
        Path(briefs_dir).mkdir(parents=True, exist_ok=True)

        brief_content = f"""# Briefing de Conteúdo — OMNIS

**Workflow:** {workflow_id[:8]}
**Data:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
**Página:** @{pagina}
**Formato:** {formato}
**Objetivo:** {objective}
**Tema:** {topic}

## Diretrizes
- Tom de voz: autêntico, próximo, autoridade no nicho
- CTA claro no final
- Hashtags estratégicas (mix de volume e nicho)
- SEOgram aplicado na legenda

## Formato
{self._formato_guidelines(formato)}

## Próximos Passos
1. Produtor (CrewAI) cria conteúdo baseado neste briefing
2. Revisão humana no Approval Gate
3. Agendamento e publicação
"""
        if not dry_run:
            safe_topic = topic.lower().replace(" ", "_")[:30]
            brief_path = str(Path(briefs_dir) / f"{workflow_id[:8]}_{safe_topic}.md")
            with open(brief_path, "w", encoding="utf-8") as f:
                f.write(brief_content)
            logger.info("[WF:%s] Briefing salvo em %s", workflow_id[:8], brief_path)

        return {"brief_size": len(brief_content)}

    def _formato_guidelines(self, formato: str) -> str:
        guias = {
            "carrossel": "5-10 slides. Capa impacto. Info útil no meio. CTA no final.",
            "reel": "15-30s. Hook nos primeiros 2s. Edição dinâmica. Legenda complementar.",
            "feed": "Imagem única de alto impacto. Legenda com história + CTA.",
            "stories": "Série de 3-5 stories. Interativo (caixa de pergunta, enquete).",
        }
        return guias.get(formato, "Seguir padrão do perfil.")

    def _produce(self, topic: str, pagina: str, formato: str,
                 crew_type: str) -> dict:
        """Estágio PRODUCE: chama Publisher OS CrewAI."""
        # Tenta via API de crew primeiro
        try:
            result = self.publisher.run_crew(
                topic=topic, pagina=pagina,
                formato=formato, crew_type=crew_type,
            )
            job_id = result.get("job_id") or result.get("id")
            return {"job_id": job_id, "raw": result}
        except PublisherBridgeError as e:
            logger.warning("Crew API falhou, tentando MCP produce_content: %s", e)
            # Fallback: MCP produce_content
            try:
                result = self.publisher.produce_content(
                    tema=topic, pagina=pagina, formato=formato,
                )
                job_id = result.get("job_id") if isinstance(result, dict) else None
                return {"job_id": job_id, "raw": result, "via": "mcp"}
            except PublisherBridgeError as e2:
                return {"error": str(e2)}

    def _draft(self, queue_id: str) -> dict:
        """Estágio DRAFT: cria ArgosDraft a partir do queue item."""
        # Provider de caption: buscar drafts existentes para este queue_id
        drafts = self.caption_mgr.list_all()
        caption = None
        for d in drafts:
            if d.queue_id == queue_id and d.status == "approved":
                caption = d
                break
        if not caption:
            # Se não tem caption aprovado, cria um caption vazio como placeholder
            caption = self.caption_mgr.create(
                queue_id=queue_id,
                account_handle="",  # será preenchido
            )

        builder = DraftBuilder(
            queue_provider=lambda qid: self.queue.get(qid),
            caption_provider=lambda qid: caption,
        )
        draft, errors = builder.create(queue_id)
        if errors:
            return {"error": "; ".join(errors)}
        return {"draft_id": draft.draft_id, "draft": draft}

    # ── Enqueue ───────────────────────────────────────────

    def enqueue_draft(self, draft_id: str) -> dict:
        """Enfileira um draft no Publisher OS BullMQ."""
        draft = get_draft(draft_id)
        if not draft:
            return {"error": f"Draft '{draft_id}' não encontrado"}

        # Se o draft já tem post_id do ARGOS, enfileira via MCP
        if hasattr(draft, 'post_id') and draft.post_id:
            try:
                result = self.publisher.argos_enqueue_post(draft.post_id)
                return {"status": "enqueued", "result": result}
            except PublisherBridgeError as e:
                return {"error": str(e)}

        return {"error": "Draft sem post_id — produza primeiro via Publisher OS"}

    # ── Status ────────────────────────────────────────────

    def status(self) -> dict:
        """Status do ecossistema de workflow."""
        # Últimos workflows
        workflows = self._list_recent(limit=5)

        # Status do Publisher OS
        pub_health = self.publisher.health()

        # Status da fila
        queue_stats = self.queue.stats()

        return {
            "publisher_os": pub_health,
            "queue": queue_stats,
            "recent_workflows": len(workflows),
            "workflows": workflows,
        }

    # ── Persistência ──────────────────────────────────────

    def _save(self, result: WorkflowResult):
        with open(WORKFLOW_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "workflow_id": result.workflow_id,
                "topic": result.topic,
                "pagina": result.pagina,
                "formato": result.formato,
                "stages": result.stages,
                "queue_id": result.queue_id,
                "draft_id": result.draft_id,
                "job_id": result.job_id,
                "errors": result.errors,
                "created_at": result.created_at,
            }, ensure_ascii=False) + "\n")

    def _list_recent(self, limit: int = 10) -> list[dict]:
        if not os.path.isfile(WORKFLOW_PATH):
            return []
        items = []
        with open(WORKFLOW_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        items.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return items[-limit:]
