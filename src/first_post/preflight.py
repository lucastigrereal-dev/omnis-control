"""First Post Preflight — 8 checks antes de publicar. P1.3a."""
from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from typing import List

from src.first_post.models import PreflightCheck, PreflightReport, PreflightStatus
from src.first_post.errors import PreflightFailedError, NoContentReadyError


class FirstPostPreflight:
    """Executa 8 checks de preflight sem publicar nada."""

    def run(self) -> PreflightReport:
        """Executa todos os checks e retorna report."""
        checks: list[PreflightCheck] = []

        checks.append(self._check_queue_items())
        checks.append(self._check_approved_content())
        checks.append(self._check_assets_ready())
        checks.append(self._check_publisher_healthy())
        checks.append(self._check_disk_space())
        checks.append(self._check_caption_complete())
        checks.append(self._check_no_placeholders())
        checks.append(self._check_accounts_active())

        passed = sum(1 for c in checks if c.passed)
        failed = sum(1 for c in checks if not c.passed)
        required_failed = [c for c in checks if not c.passed and c.required]
        blocked = len(required_failed)

        can_publish = blocked == 0
        ready_items = self._count_ready_items()

        if blocked > 0:
            overall = PreflightStatus.BLOCKED
        elif failed > 0:
            overall = PreflightStatus.PARTIAL
        elif ready_items == 0:
            overall = PreflightStatus.EMPTY
        else:
            overall = PreflightStatus.READY

        if blocked > 0:
            next_action = f"Corrija {blocked} bloqueio(s) antes de publicar"
        elif ready_items == 0:
            next_action = "Gere conteudo: omnis workflow run --pagina <handle> --formato carrossel \"tema\""
        elif can_publish:
            next_action = "Conteudo pronto! Lucas precisa autorizar publicacao (NO-GO sem humano acordado)"
        else:
            next_action = "Resolva avisos e revise o conteudo"

        return PreflightReport(
            overall_status=overall,
            passed=passed,
            failed=failed,
            blocked=blocked,
            checks=checks,
            can_publish=can_publish,
            ready_items=ready_items,
            next_action=next_action,
            checked_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    def _check_queue_items(self) -> PreflightCheck:
        """Verifica se ha itens na fila de publicacao."""
        try:
            from src.content_queue import Queue as CQQueue
            queue = CQQueue()
            items = queue.list_all()
            scheduled = [i for i in items if i.status in ("approved", "scheduled")]
            passed = len(scheduled) > 0
            return PreflightCheck(
                check_id="queue_items",
                label="Itens na fila de publicacao",
                passed=passed,
                required=True,
                detail=f"{len(scheduled)} aprovados/agendados de {len(items)} totais",
                recommendation="Gere fila: omnis queue generate --apply" if not passed else "",
            )
        except Exception as e:
            return PreflightCheck(
                check_id="queue_items",
                label="Itens na fila de publicacao",
                passed=False,
                required=True,
                detail=f"Erro: {e}",
                recommendation="Verifique se Content Queue esta funcionando",
            )

    def _check_approved_content(self) -> PreflightCheck:
        """Verifica se ha drafts aprovados."""
        try:
            from src.caption_approval import DraftsManager
            from src.caption_approval.models import DraftStatus
            dm = DraftsManager()
            all_drafts = dm.list_all()
            approved = [d for d in all_drafts if d.status == DraftStatus.APPROVED]
            passed = len(approved) > 0
            return PreflightCheck(
                check_id="approved_content",
                label="Drafts aprovados",
                passed=passed,
                required=True,
                detail=f"{len(approved)} aprovados de {len(all_drafts)} drafts",
                recommendation="Aprove drafts: omnis approvals approve <draft_id>" if not passed else "",
            )
        except Exception as e:
            return PreflightCheck(
                check_id="approved_content",
                label="Drafts aprovados",
                passed=False,
                required=True,
                detail=f"Erro: {e}",
                recommendation="Verifique caption_approval",
            )

    def _check_assets_ready(self) -> PreflightCheck:
        """Verifica se assets estao atribuidos aos slots."""
        try:
            from src.content_queue import Queue as CQQueue
            queue = CQQueue()
            items = queue.list_all()
            approved = [i for i in items if i.status in ("approved", "scheduled", "caption_ready")]
            with_assets = [i for i in approved if i.asset_id]
            passed = len(with_assets) > 0 if approved else False
            return PreflightCheck(
                check_id="assets_ready",
                label="Assets atribuidos aos slots",
                passed=passed,
                required=False,
                detail=f"{len(with_assets)} com asset de {len(approved)} slots aprovados",
                recommendation="Atribua assets: omnis queue assign <queue_id> <asset_id>" if not passed and approved else "",
            )
        except Exception as e:
            return PreflightCheck(
                check_id="assets_ready",
                label="Assets atribuidos",
                passed=False,
                required=False,
                detail=f"Erro: {e}",
                recommendation="",
            )

    def _check_publisher_healthy(self) -> PreflightCheck:
        """Publisher OS :8000 responde."""
        import urllib.request
        try:
            req = urllib.request.Request("http://localhost:8000/health", method="GET")
            res = urllib.request.urlopen(req, timeout=5)
            passed = res.status == 200
            return PreflightCheck(
                check_id="publisher_healthy",
                label="Publisher OS health",
                passed=passed,
                required=True,
                detail=f"HTTP {res.status}" if passed else f"HTTP {res.status}",
                recommendation="Inicie publisher-os" if not passed else "",
            )
        except Exception as e:
            return PreflightCheck(
                check_id="publisher_healthy",
                label="Publisher OS health",
                passed=False,
                required=True,
                detail=f"Offline: {e}",
                recommendation="Inicie publisher-os: cd ~/publisher-os && docker compose up -d publisher-core",
            )

    def _check_disk_space(self) -> PreflightCheck:
        """Disco >= 5% livre."""
        try:
            import shutil
            usage = shutil.disk_usage(os.path.expanduser("~"))
            pct = (usage.free / usage.total) * 100
            passed = pct >= 5.0
            return PreflightCheck(
                check_id="disk_space",
                label="Espaco em disco >= 5%",
                passed=passed,
                required=True,
                detail=f"{pct:.1f}% livre ({usage.free // (1024**3)}GB)",
                recommendation="Libere espaco em disco" if not passed else "",
            )
        except Exception as e:
            return PreflightCheck(
                check_id="disk_space",
                label="Espaco em disco",
                passed=False,
                required=True,
                detail=f"Erro: {e}",
                recommendation="Verifique disco manualmente",
            )

    def _check_caption_complete(self) -> PreflightCheck:
        """Verifica se aprovados tem legenda preenchida."""
        try:
            from src.caption_approval import DraftsManager
            from src.caption_approval.models import DraftStatus
            dm = DraftsManager()
            all_drafts = dm.list_all()
            approved = [d for d in all_drafts if d.status == DraftStatus.APPROVED]
            if not approved:
                return PreflightCheck(
                    check_id="caption_complete",
                    label="Legendas preenchidas nos aprovados",
                    passed=False,
                    required=True,
                    detail="Nenhum draft aprovado encontrado",
                    recommendation="Aprove drafts primeiro",
                )
            with_text = [d for d in approved if d.caption_text and len(d.caption_text.strip()) > 10]
            passed = len(with_text) == len(approved)
            return PreflightCheck(
                check_id="caption_complete",
                label="Legendas preenchidas nos aprovados",
                passed=passed,
                required=True,
                detail=f"{len(with_text)}/{len(approved)} com legenda completa",
                recommendation="Preencha legendas nos drafts sem texto" if not passed else "",
            )
        except Exception as e:
            return PreflightCheck(
                check_id="caption_complete",
                label="Legendas preenchidas",
                passed=False,
                required=True,
                detail=f"Erro: {e}",
                recommendation="",
            )

    def _check_no_placeholders(self) -> PreflightCheck:
        """Verifica se nao ha placeholders [BOT] nas legendas."""
        try:
            from src.caption_approval import DraftsManager
            from src.caption_approval.models import DraftStatus
            dm = DraftsManager()
            all_drafts = dm.list_all()
            approved = [d for d in all_drafts if d.status == DraftStatus.APPROVED]
            if not approved:
                return PreflightCheck(
                    check_id="no_placeholders",
                    label="Sem placeholders [BOT] nas legendas",
                    passed=True,
                    required=True,
                    detail="Nenhum draft aprovado para verificar",
                    recommendation="",
                )
            bad = [d for d in approved if "[BOT]" in (d.caption_text or "")]
            passed = len(bad) == 0
            return PreflightCheck(
                check_id="no_placeholders",
                label="Sem placeholders [BOT] nas legendas",
                passed=passed,
                required=True,
                detail=f"{len(bad)} drafts com [BOT]" if not passed else "Nenhum placeholder encontrado",
                recommendation="Substitua [BOT] por texto real nos drafts" if not passed else "",
            )
        except Exception as e:
            return PreflightCheck(
                check_id="no_placeholders",
                label="Sem placeholders [BOT]",
                passed=False,
                required=True,
                detail=f"Erro: {e}",
                recommendation="",
            )

    def _check_accounts_active(self) -> PreflightCheck:
        """Verifica se ha contas ativas para publicacao."""
        try:
            from src.content_queue import AccountRegistry
            reg = AccountRegistry()
            active = reg.list_active()
            passed = len(active) >= 1
            return PreflightCheck(
                check_id="accounts_active",
                label="Contas ativas para publicacao",
                passed=passed,
                required=True,
                detail=f"{len(active)} contas ativas" if passed else "Nenhuma conta ativa",
                recommendation="Ative contas: omnis accounts update @handle --priority high" if not passed else "",
            )
        except Exception as e:
            return PreflightCheck(
                check_id="accounts_active",
                label="Contas ativas",
                passed=False,
                required=True,
                detail=f"Erro: {e}",
                recommendation="",
            )

    def _count_ready_items(self) -> int:
        """Conta quantos itens estao prontos para publicar."""
        try:
            from src.content_queue import Queue as CQQueue
            from src.caption_approval import DraftsManager
            from src.caption_approval.models import DraftStatus
            queue = CQQueue()
            dm = DraftsManager()
            items = queue.list_all()
            all_drafts = dm.list_all()
            approved_draft_ids = {d.queue_id for d in all_drafts if d.status == DraftStatus.APPROVED}
            count = 0
            for item in items:
                if item.status in ("approved", "scheduled", "caption_ready") and item.queue_id in approved_draft_ids:
                    count += 1
            return count
        except Exception:
            return 0


_preflight: FirstPostPreflight | None = None


def get_preflight() -> FirstPostPreflight:
    global _preflight
    if _preflight is None:
        _preflight = FirstPostPreflight()
    return _preflight
