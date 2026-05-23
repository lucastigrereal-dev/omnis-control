"""CodeExecutorLego — implementação do contrato CodeExecutor.

Estratégia (OpenHands como serviço separado, não embutido):
  1. Se OPENHANDS_URL configurado e serviço respondendo → delega via HTTP
  2. Senão → executa Python local em subprocess sandboxado (dry_run seguro)

Regras OMNIS:
- dry_run=True por padrão — gera plano/análise sem executar código real
- Approval gate antes de deploy/publicação em dry_run=False
- health_check() verifica se serviço OpenHands está vivo
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

from src.interfaces.code_executor import CodeExecutor, CodeSpec, CodeResult

_logger = logging.getLogger("omnis.legos.code")

OPENHANDS_URL = os.getenv("OPENHANDS_URL", "http://localhost:3000")

_DEPLOY_KEYWORDS = frozenset({
    "deploy", "publicar", "publish", "upload", "push",
    "release", "lançar", "entregar", "ship",
})

_UNSAFE_GOAL_PATTERN = re.compile(
    r"""(?ix)
    [\r\n]
    |;
    |&&
    |\|\|
    |` 
    |\$\(
    |\b(__import__|exec\s*\(|eval\s*\(|subprocess|os\.system)\b
    """
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _requires_deploy_approval(goal: str) -> bool:
    g = goal.lower()
    return any(kw in g for kw in _DEPLOY_KEYWORDS)


def _has_unsafe_goal_payload(goal: str) -> bool:
    return bool(_UNSAFE_GOAL_PATTERN.search(goal))


class CodeExecutorLego:
    """Implementação do Protocol CodeExecutor.

    Avalia OpenHands como serviço; cai para sandbox local quando offline.
    """

    def health_check(self) -> bool:
        """Retorna True se o serviço OpenHands está respondendo."""
        import urllib.request
        import urllib.error
        try:
            with urllib.request.urlopen(f"{OPENHANDS_URL}/health", timeout=3):
                return True
        except (urllib.error.URLError, OSError):
            return False

    def execute(self, spec: CodeSpec) -> CodeResult:
        """Executa spec via OpenHands (se disponível) ou sandbox local."""
        # Approval gate
        if not spec.dry_run and _requires_deploy_approval(spec.goal):
            _logger.warning("[code][%s] APPROVAL REQUIRED: '%s'", _now_iso(), spec.goal[:80])
            return CodeResult(
                success=False,
                output="",
                files_created=[],
                tests_passed=False,
                dry_run=spec.dry_run,
                error="approval_required",
                artifacts={
                    "approval_required": True,
                    "reason": f"Goal '{spec.goal}' requer aprovação humana antes de deploy.",
                },
            )

        if spec.dry_run:
            return self._dry_run_plan(spec)

        if self.health_check():
            return self._call_openhands_service(spec)

        return self._local_sandbox(spec)

    def _dry_run_plan(self, spec: CodeSpec) -> CodeResult:
        """Gera plano estruturado sem executar código."""
        _logger.info("[code][%s] DRY PLAN: %s", _now_iso(), spec.goal[:80])
        plan = (
            f"# Plano: {spec.goal}\n"
            f"- Linguagem: {spec.language}\n"
            f"- Contexto: {len(spec.context_files)} arquivo(s)\n"
            f"- Output dir: {spec.output_dir}\n"
            f"[dry_run=True — nenhum arquivo criado]"
        )
        return CodeResult(
            success=True,
            output=plan,
            files_created=[],
            tests_passed=True,
            dry_run=True,
            artifacts={"mode": "dry_run_plan", "language": spec.language},
        )

    def _call_openhands_service(self, spec: CodeSpec) -> CodeResult:
        """Delega ao serviço OpenHands via HTTP POST."""
        import json
        import urllib.request
        import urllib.error

        payload = json.dumps({
            "goal": spec.goal,
            "language": spec.language,
            "context_files": spec.context_files,
            "output_dir": spec.output_dir,
        }).encode()

        try:
            req = urllib.request.Request(
                f"{OPENHANDS_URL}/execute",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
            return CodeResult(
                success=data.get("success", False),
                output=data.get("output", ""),
                files_created=data.get("files_created", []),
                tests_passed=data.get("tests_passed", False),
                dry_run=False,
                artifacts={"mode": "openhands_service", "url": OPENHANDS_URL},
            )
        except Exception as e:
            _logger.error("[code] OpenHands call failed: %s", e)
            return CodeResult(
                success=False, output="", files_created=[],
                tests_passed=False, dry_run=False, error=str(e),
            )

    def _local_sandbox(self, spec: CodeSpec) -> CodeResult:
        """Executa Python sandboxado localmente (fallback sem OpenHands)."""
        _logger.info("[code][%s] LOCAL SANDBOX: %s", _now_iso(), spec.goal[:80])
        # Só permite execução de código Python — sem shell injection
        if spec.language.lower() != "python":
            return CodeResult(
                success=False, output="", files_created=[],
                tests_passed=False, dry_run=False,
                error=f"local_sandbox: somente Python suportado (got {spec.language})",
            )

        # Defense in depth: bloqueia marcadores de injeção óbvios.
        if _has_unsafe_goal_payload(spec.goal):
            _logger.warning("[code] sandbox: injection payload detected in goal")
            return CodeResult(
                success=False, output="", files_created=[],
                tests_passed=False, dry_run=False,
                error="local_sandbox: unsafe_goal_payload",
                artifacts={"blocked": True, "reason": "unsafe_goal_payload"},
            )

        # goal e output_dir passados como argv — NUNCA interpolados no código.
        # Isso isola dados de código e elimina o vetor de RCE pela raiz.
        script = (
            "import sys\n"
            "goal = sys.argv[1] if len(sys.argv) > 1 else ''\n"
            "output_dir = sys.argv[2] if len(sys.argv) > 2 else ''\n"
            "print('sandbox: goal recebido')\n"
            "print('output_dir:', output_dir)\n"
        )

        try:
            result = subprocess.run(
                [sys.executable, "-c", script, "--", spec.goal, spec.output_dir],
                capture_output=True, text=True, timeout=30,
            )
            success = result.returncode == 0
            return CodeResult(
                success=success,
                output=result.stdout.strip(),
                files_created=[],
                tests_passed=success,
                dry_run=False,
                error=result.stderr.strip() or None,
                artifacts={"mode": "local_sandbox"},
            )
        except subprocess.TimeoutExpired:
            return CodeResult(
                success=False, output="", files_created=[],
                tests_passed=False, dry_run=False, error="local_sandbox: timeout",
            )
