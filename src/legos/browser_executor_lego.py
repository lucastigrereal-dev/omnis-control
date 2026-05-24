"""BrowserExecutorLego — implementação do contrato BrowserExecutor usando Playwright.

Extrai APENAS o núcleo de navegação/extração do Playwright.
Não inclui cloud, stealth pago, UI desktop ou qualquer dep além de playwright.

Regras OMNIS:
- dry_run=True por padrão — navega e extrai, nunca clica em ações críticas
- 1 browser por vez (semáforo de RAM — Chrome consome ~400MB)
- Approval gate antes de ações críticas em modo real (login, compra, envio)
- Loga no padrão OMNIS (datetime ISO + prefixo [browser])
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any

from src.interfaces.browser_executor import BrowserExecutor, BrowserTask, BrowserResult
from src.computer_use.sandbox import SecuritySandbox

_logger = logging.getLogger("omnis.legos.browser")

# ── RAM guard: 1 browser ativo por vez ───────────────────────────────────────
_BROWSER_SEMAPHORE = threading.Semaphore(1)

# ── Ações que exigem approval gate antes de executar ─────────────────────────
_CRITICAL_KEYWORDS = frozenset({
    "login", "entrar", "senha", "password", "sign in",
    "comprar", "buy", "purchase", "checkout", "pagar", "pagamento",
    "enviar", "send", "submit", "postar", "publicar", "post",
    "deletar", "delete", "remover", "remove",
    "cadastrar", "register", "criar conta",
})


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(msg: str) -> None:
    _logger.info("[browser][%s] %s", _now_iso(), msg)


def _is_critical(goal: str) -> bool:
    goal_lower = goal.lower()
    return any(kw in goal_lower for kw in _CRITICAL_KEYWORDS)


class BrowserExecutorLego:
    """Implementação do Protocol BrowserExecutor usando Playwright.

    Instancie uma vez e reutilize. Thread-safe via semáforo global.
    """

    def __init__(self) -> None:
        self._sandbox = SecuritySandbox(strict=True)

    def health_check(self) -> bool:
        """Retorna True se playwright + chromium estão disponíveis."""
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser.close()
            return True
        except Exception:
            return False

    def run(self, spec: "LegoCogSpec") -> "LegoCogResult":
        """Implementa LegoCog.run() — converte LegoCogSpec → BrowserTask."""
        from src.legos.protocol import LegoCogSpec, LegoCogResult  # noqa: F401
        task = BrowserTask(
            url=spec.payload.get("url", "https://example.com"),
            goal=spec.goal,
            dry_run=spec.dry_run,
        )
        result = self.execute(task)
        return LegoCogResult(
            success=result.success,
            output=result.output,
            dry_run=result.dry_run,
            error=result.error or "",
            artifacts=result.artifacts,
        )

    def execute(self, task: BrowserTask) -> BrowserResult:
        """Executa uma tarefa web e retorna resultado estruturado.

        dry_run=True (padrão): navega e extrai texto — sem clicks críticos.
        dry_run=False: também interage, mas bloqueia ações críticas sem approval.
        """
        # Approval gate — bloqueia antes de qualquer IO
        if not task.dry_run and _is_critical(task.goal):
            _log(f"APPROVAL REQUIRED for critical goal: '{task.goal[:80]}'")
            return BrowserResult(
                success=False,
                output="",
                url_visited=task.url,
                dry_run=task.dry_run,
                error="approval_required",
                artifacts={
                    "approval_required": True,
                    "reason": f"Goal '{task.goal}' contém ação crítica. Aprovação humana necessária.",
                },
            )

        # Sandbox validation
        try:
            self._sandbox.validate_url(task.url)
        except Exception as e:
            return BrowserResult(
                success=False,
                output="",
                url_visited=task.url,
                dry_run=task.dry_run,
                error=f"sandbox_blocked: {e}",
            )

        acquired = _BROWSER_SEMAPHORE.acquire(timeout=task.timeout_seconds)
        if not acquired:
            return BrowserResult(
                success=False,
                output="",
                url_visited=task.url,
                dry_run=task.dry_run,
                error="browser_semaphore_timeout: outro browser em execução",
            )

        try:
            return self._run_browser(task)
        finally:
            _BROWSER_SEMAPHORE.release()

    def _run_browser(self, task: BrowserTask) -> BrowserResult:
        """Executa o playwright dentro do semáforo."""
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

        _log(f"{'[DRY]' if task.dry_run else '[REAL]'} {task.goal[:80]} → {task.url}")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_default_timeout(task.timeout_seconds * 1000)

                page.goto(task.url, wait_until="domcontentloaded")
                title = page.title()
                body_text = page.inner_text("body")[:2000]

                artifacts: dict[str, Any] = {
                    "title": title,
                    "char_count": len(body_text),
                }

                browser.close()

            _log(f"OK — title='{title}', {len(body_text)} chars extracted")
            return BrowserResult(
                success=True,
                output=body_text,
                url_visited=task.url,
                dry_run=task.dry_run,
                artifacts=artifacts,
            )

        except PWTimeout:
            _log(f"TIMEOUT after {task.timeout_seconds}s")
            return BrowserResult(
                success=False,
                output="",
                url_visited=task.url,
                dry_run=task.dry_run,
                error=f"timeout after {task.timeout_seconds}s",
            )
        except Exception as e:
            _log(f"ERROR: {e}")
            return BrowserResult(
                success=False,
                output="",
                url_visited=task.url,
                dry_run=task.dry_run,
                error=str(e),
            )
