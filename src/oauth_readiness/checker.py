"""OAuth Readiness Checker — agrega 12 checks em report unico. P1.2a."""
from __future__ import annotations

from datetime import datetime, timezone

from src.oauth_readiness.models import OAuthReadinessCheck, OAuthReadinessReport, OAuthReadinessStatus
from src.oauth_readiness.checklist import get_all_checks


class OAuthReadinessChecker:
    """Executa 12 precondicoes e gera report agregado.

    Nao le .env, nao chama Meta, nao executa OAuth real.
    """

    def check_all(self) -> OAuthReadinessReport:
        """Executa todos os 12 checks e retorna report."""
        check_funcs = get_all_checks()
        results: list[OAuthReadinessCheck] = []

        for fn in check_funcs:
            try:
                result = fn()
            except Exception as exc:
                result = OAuthReadinessCheck(
                    check_id=fn.__name__.replace("_check_", ""),
                    label=fn.__doc__ or fn.__name__,
                    passed=False,
                    required=True,
                    status=OAuthReadinessStatus.FAILED,
                    detail=f"Check nao executado: {exc}",
                    recommendation="Investigue o erro e tente novamente",
                )
            results.append(result)

        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        required_failed = [r for r in results if not r.passed and r.required]
        blocked_by_required = len(required_failed)

        can_proceed = blocked_by_required == 0

        human_required = [r for r in results if r.status == OAuthReadinessStatus.HUMAN_REQUIRED and not r.passed]
        has_human_gates = len(human_required) > 0

        if blocked_by_required > 0:
            if has_human_gates and all(
                r.status == OAuthReadinessStatus.HUMAN_REQUIRED
                for r in required_failed
            ):
                overall = OAuthReadinessStatus.HUMAN_REQUIRED
            elif any(r.status == OAuthReadinessStatus.FAILED for r in required_failed):
                overall = OAuthReadinessStatus.FAILED
            else:
                overall = OAuthReadinessStatus.BLOCKED
        elif failed > 0:
            overall = OAuthReadinessStatus.READY
        else:
            overall = OAuthReadinessStatus.READY

        # Determine next_action
        if has_human_gates:
            human_labels = [r.label for r in human_required]
            next_action = (
                f"Lucas precisa preencher {len(human_required)} variavel(is) no .env: "
                f"{', '.join(human_labels)}. "
                f"Depois rodar: omnis oauth readiness"
            )
        elif blocked_by_required > 0:
            failed_ids = [r.check_id for r in required_failed]
            next_action = f"Corrija os checks bloqueantes antes de prosseguir: {', '.join(failed_ids)}"
        elif can_proceed:
            next_action = "Todos os checks passaram. Execute 'omnis oauth start' para iniciar o fluxo OAuth."
        else:
            next_action = "Corrija os avisos antes de prosseguir."

        return OAuthReadinessReport(
            overall_status=overall,
            total_checks=len(results),
            passed=passed,
            failed=failed,
            blocked_by_required=blocked_by_required,
            checks=results,
            can_proceed=can_proceed,
            next_action=next_action,
            checked_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
