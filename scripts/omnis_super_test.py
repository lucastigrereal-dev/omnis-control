"""
OMNIS SUPER TEST — Diagnostic Only (Modo 1)
============================================

Objetivo: testar TUDO, identificar TUDO que falta/quebrou, gerar relatório completo
com fixes sugeridos prontos pra colar.

NÃO MEXE EM NADA. NÃO COMMITA. NÃO CORRIGE.

Tu lê o relatório, decide o que aprovar, depois Sonnet aplica fix por fix.

Uso:
    python scripts/omnis_super_test.py
    python scripts/omnis_super_test.py --quick  # pula testes longos
    python scripts/omnis_super_test.py --no-cli  # pula testes de CLI

Saída: docs/super_test/RELATORIO_<timestamp>.md

Filosofia: Lucas Tigre — construir tudo, testar tudo, validar antes de plugar.
Feynman: "Cada bug é uma decisão consciente do humano".
"""
from __future__ import annotations

import argparse
import io
import json
import os
import platform
import re
import subprocess
import sys

# Fix Windows terminal encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = REPO_ROOT / "docs" / "super_test"
TIMEOUT_SHORT = 30
TIMEOUT_LONG = 300


# ============================================================================
# MODELO DE RESULTADO
# ============================================================================

@dataclass
class CheckResult:
    """Resultado de uma verificação individual."""
    name: str
    category: str  # "critical" | "important" | "cosmetic"
    status: str    # "ok" | "warn" | "fail" | "skip"
    summary: str
    details: str = ""
    suggested_fix: str | None = None
    fix_command: str | None = None
    duration_ms: int = 0


@dataclass
class SuperTestReport:
    """Relatório consolidado."""
    timestamp: str
    duration_total_s: float = 0.0
    repo_root: str = ""
    git_branch: str = ""
    git_commit: str = ""
    python_version: str = ""
    platform: str = ""
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def stats(self) -> dict[str, int]:
        s = {"ok": 0, "warn": 0, "fail": 0, "skip": 0}
        for c in self.checks:
            s[c.status] = s.get(c.status, 0) + 1
        return s


# ============================================================================
# HELPERS
# ============================================================================

def run_cmd(cmd: list[str] | str, timeout: int = TIMEOUT_SHORT, cwd: Path | None = None) -> tuple[int, str, str]:
    """Executa comando e retorna (returncode, stdout, stderr). Nunca raise."""
    try:
        is_str = isinstance(cmd, str)
        result = subprocess.run(
            cmd,
            shell=is_str,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or REPO_ROOT,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"TIMEOUT após {timeout}s"
    except Exception as e:
        return -2, "", f"EXCEPTION: {e}"


def now_ms() -> int:
    return int(time.time() * 1000)


def banner(text: str) -> None:
    print(f"\n{'─' * 70}")
    print(f"  {text}")
    print(f"{'─' * 70}")


def status_icon(status: str) -> str:
    return {"ok": "✅", "warn": "🟡", "fail": "❌", "skip": "⏭️"}.get(status, "?")


# ============================================================================
# FASE 0 — METADATA DO AMBIENTE
# ============================================================================

def collect_environment(report: SuperTestReport) -> None:
    """Coleta info do ambiente. Não tem 'check' propriamente — só metadata."""
    banner("FASE 0 — Ambiente")
    report.repo_root = str(REPO_ROOT)
    report.python_version = sys.version.split()[0]
    report.platform = f"{platform.system()} {platform.release()}"

    rc, out, _ = run_cmd(["git", "branch", "--show-current"])
    report.git_branch = out.strip() if rc == 0 else "unknown"

    rc, out, _ = run_cmd(["git", "log", "-1", "--format=%H %s"])
    report.git_commit = out.strip() if rc == 0 else "unknown"

    print(f"  Repo:    {report.repo_root}")
    print(f"  Python:  {report.python_version}")
    print(f"  OS:      {report.platform}")
    print(f"  Branch:  {report.git_branch}")
    print(f"  Commit:  {report.git_commit[:80]}")


# ============================================================================
# FASE 1 — VERIFICAÇÕES DE CRÍTICAS (git/repo/python)
# ============================================================================

def check_git_clean(report: SuperTestReport) -> None:
    start = now_ms()
    rc, out, err = run_cmd(["git", "status", "--short"])
    dirty = bool(out.strip())
    if rc != 0:
        report.checks.append(CheckResult(
            "git_status", "critical", "fail",
            "git status falhou",
            details=err,
            duration_ms=now_ms() - start,
        ))
        return

    if dirty:
        report.checks.append(CheckResult(
            "git_status", "important", "warn",
            f"{len(out.strip().splitlines())} arquivo(s) não commitado(s)",
            details=out.strip(),
            suggested_fix=(
                "Revisar arquivos não commitados:\n"
                "  git status --short\n"
                "  git diff <arquivo>\n"
                "Decidir: commitar ou descartar com 'git checkout -- <arquivo>'."
            ),
            duration_ms=now_ms() - start,
        ))
    else:
        report.checks.append(CheckResult(
            "git_status", "important", "ok",
            "git status limpo",
            duration_ms=now_ms() - start,
        ))


def check_branch_master(report: SuperTestReport) -> None:
    start = now_ms()
    rc, out, _ = run_cmd(["git", "branch", "--show-current"])
    branch = out.strip() if rc == 0 else "unknown"
    if branch == "master":
        report.checks.append(CheckResult(
            "git_branch", "critical", "ok",
            f"branch correta: {branch}",
            duration_ms=now_ms() - start,
        ))
    else:
        report.checks.append(CheckResult(
            "git_branch", "important", "warn",
            f"branch atual: {branch} (esperado: master)",
            suggested_fix="git checkout master",
            duration_ms=now_ms() - start,
        ))


def check_python_version(report: SuperTestReport) -> None:
    start = now_ms()
    major, minor = sys.version_info.major, sys.version_info.minor
    if major == 3 and minor >= 10:
        report.checks.append(CheckResult(
            "python_version", "critical", "ok",
            f"Python {major}.{minor} OK",
            duration_ms=now_ms() - start,
        ))
    else:
        report.checks.append(CheckResult(
            "python_version", "critical", "fail",
            f"Python {major}.{minor} pode ter incompatibilidades",
            duration_ms=now_ms() - start,
        ))


# ============================================================================
# FASE 2 — VERIFICAÇÕES DA SUITE DE TESTES
# ============================================================================

def check_pytest_full(report: SuperTestReport) -> None:
    """Roda pytest completo, captura passing/failing."""
    start = now_ms()
    print("  Rodando pytest... pode demorar ~4 min")
    rc, out, err = run_cmd(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"],
        timeout=TIMEOUT_LONG,
    )
    duration = now_ms() - start

    # Parse "X failed, Y passed in Z s"
    match = re.search(r"(\d+)\s+failed,\s*(\d+)\s+passed", out)
    if match:
        failed, passed = int(match.group(1)), int(match.group(2))
        total = failed + passed
        details = f"{passed}/{total} passing — {failed} failures"
        # Extrair nomes dos testes que falharam
        fail_lines = [ln for ln in out.splitlines() if ln.startswith("FAILED")]
        if fail_lines:
            details += "\n\nTestes que falharam:\n" + "\n".join(fail_lines[:10])

        status = "fail" if failed > 0 else "ok"
        report.checks.append(CheckResult(
            "pytest_suite", "critical", status,
            f"{passed}/{total} testes passando ({failed} falhas)",
            details=details,
            duration_ms=duration,
        ))
    else:
        # Match alternativo: só "X passed"
        match = re.search(r"(\d+)\s+passed", out)
        if match:
            passed = int(match.group(1))
            report.checks.append(CheckResult(
                "pytest_suite", "critical", "ok",
                f"{passed} testes passando — 0 falhas",
                details=out[-500:],
                duration_ms=duration,
            ))
        else:
            report.checks.append(CheckResult(
                "pytest_suite", "critical", "fail",
                "não consegui parsear saída do pytest",
                details=(out + "\n" + err)[-1000:],
                duration_ms=duration,
            ))


def check_deprecation_warnings(report: SuperTestReport) -> None:
    """Conta DeprecationWarning de datetime.utcnow()."""
    start = now_ms()
    rc, out, _ = run_cmd(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no", "-W", "always"],
        timeout=TIMEOUT_LONG,
    )

    utcnow_count = out.count("datetime.datetime.utcnow() is deprecated")
    utcfromtimestamp_count = out.count("datetime.datetime.utcfromtimestamp() is deprecated")
    total = utcnow_count + utcfromtimestamp_count

    if total > 0:
        # Encontrar arquivos afetados
        files_affected = set()
        for ln in out.splitlines():
            m = re.search(r"(src[\\/][\w\\/]+\.py):\d+:", ln)
            if m:
                files_affected.add(m.group(1).replace("\\", "/"))

        files_list = sorted(files_affected)
        fix_diff = """
# FIX para BUG #2 (datetime.utcnow deprecation)
# Aplicar em CADA arquivo da lista abaixo:

# ANTES:
from datetime import datetime
timestamp = datetime.utcnow().isoformat()
timestamp = datetime.utcfromtimestamp(record.created).isoformat()

# DEPOIS:
from datetime import datetime, timezone
timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat().replace("+00:00", "Z")

# Comando find-replace seguro (rode depois de revisar cada arquivo):
# (No PowerShell — adapta se for Linux)
# Get-ChildItem -Recurse -Include *.py | ForEach-Object {
#     (Get-Content $_) -replace 'datetime\\.utcnow\\(\\)', 'datetime.now(timezone.utc)' | Set-Content $_
# }
"""
        report.checks.append(CheckResult(
            "deprecation_datetime_utcnow", "cosmetic", "warn",
            f"{total} DeprecationWarnings em {len(files_list)} arquivos",
            details=f"Arquivos afetados:\n" + "\n".join(f"  - {f}" for f in files_list),
            suggested_fix=fix_diff,
            duration_ms=now_ms() - start,
        ))
    else:
        report.checks.append(CheckResult(
            "deprecation_datetime_utcnow", "cosmetic", "ok",
            "0 deprecation warnings de datetime",
            duration_ms=now_ms() - start,
        ))


# ============================================================================
# FASE 3 — VERIFICAÇÕES DE CLI (smoke test dos comandos)
# ============================================================================

CLI_COMMANDS_TO_TEST = [
    ("status", "status do ecossistema"),
    ("doctor", "diagnóstico JSON"),
    ("briefing", "briefing diário"),
    ("skills", "lista skills"),
    ("queue list", "lista fila"),
    ("captions list", "lista captions"),
    ("creative status", "creative production"),
    ("publisher status", "publisher dry-run"),
    ("forge list", "capability forge"),
    ("pipeline status", "pipeline local"),
]


def check_cli_commands(report: SuperTestReport) -> None:
    """Roda cada comando do CLI e captura se quebrou."""
    for cmd, descr in CLI_COMMANDS_TO_TEST:
        start = now_ms()
        rc, out, err = run_cmd(
            f"{sys.executable} omnis.py {cmd}",
            timeout=TIMEOUT_SHORT,
        )
        duration = now_ms() - start

        if rc == 0:
            report.checks.append(CheckResult(
                f"cli_{cmd.replace(' ', '_')}", "important", "ok",
                f"omnis {cmd} → OK ({descr})",
                duration_ms=duration,
            ))
        elif rc == -1:
            report.checks.append(CheckResult(
                f"cli_{cmd.replace(' ', '_')}", "important", "warn",
                f"omnis {cmd} → TIMEOUT",
                duration_ms=duration,
            ))
        else:
            report.checks.append(CheckResult(
                f"cli_{cmd.replace(' ', '_')}", "important", "fail",
                f"omnis {cmd} → exit code {rc}",
                details=(err + "\n" + out)[-500:],
                duration_ms=duration,
            ))


# ============================================================================
# FASE 4 — VERIFICAÇÃO DO BUG #1 (TRUNCAMENTO DE IDs)
# ============================================================================

def check_id_truncation_bug(report: SuperTestReport) -> None:
    """
    BUG #1 — captions list mostra IDs truncados (8 chars), pipeline dry-run quer ID completo.

    Estratégia: pegar o caption aprovado, comparar lengths.
    """
    start = now_ms()
    rc, out, _ = run_cmd(
        f"{sys.executable} omnis.py captions list",
        timeout=TIMEOUT_SHORT,
    )

    if rc != 0:
        report.checks.append(CheckResult(
            "bug_id_truncation", "important", "skip",
            "não consegui rodar captions list — bug não verificável agora",
            duration_ms=now_ms() - start,
        ))
        return

    # Procura por linha com 'approved' e extrai os IDs (8 chars hex)
    approved_lines = [ln for ln in out.splitlines() if "approved" in ln.lower()]
    if not approved_lines:
        report.checks.append(CheckResult(
            "bug_id_truncation", "cosmetic", "skip",
            "nenhum caption aprovado encontrado para teste",
            duration_ms=now_ms() - start,
        ))
        return

    # Detecta padrão de IDs curtos (8 chars hex) na tabela
    short_id_pattern = re.compile(r"\b[a-f0-9]{8}\b")
    matches = short_id_pattern.findall(approved_lines[0])

    fix_code = """
# FIX para BUG #1 (truncamento de IDs)
# Localização provável: src/cli_commands/pipeline_cmd.py
# Função que recebe o queue_id

# ANTES:
def dry_run(queue_id: str):
    item = service.get_queue_item(queue_id)  # match exato — falha com prefix
    if not item:
        return blocked("CAPTION_NOT_APPROVED")

# DEPOIS (prefix matching):
def dry_run(queue_id: str):
    item = service.get_queue_item(queue_id)
    if not item:
        # Tenta prefix match
        all_items = service.list_queue_items()
        matches = [i for i in all_items if i.id.startswith(queue_id)]
        if len(matches) == 1:
            item = matches[0]
        elif len(matches) > 1:
            return blocked(f"AMBIGUOUS_ID: {len(matches)} matches for '{queue_id}'")
        else:
            return blocked("QUEUE_ITEM_NOT_FOUND")

# Aplicar mesma lógica em:
# - src/cli_commands/pipeline_cmd.py (dry-run)
# - src/cli_commands/captions_cmd.py (show, approve, reject)
# - qualquer outro lugar que recebe ID via CLI

# Teste manual após fix:
# python omnis.py pipeline dry-run 0b79aa1c     # ID curto, deve funcionar
# python omnis.py pipeline dry-run 0b79aa1cd7fc # ID completo, deve continuar funcionando
"""

    report.checks.append(CheckResult(
        "bug_id_truncation", "important", "warn",
        f"IDs aparecem truncados a 8 chars na listagem ({len(matches)} encontrados)",
        details=(
            f"Linha exemplo: {approved_lines[0][:200]}\n"
            f"IDs detectados (8 chars): {matches[:3]}\n"
            f"Bug confirmado pelo Lucas: pipeline dry-run com ID curto retorna CAPTION_NOT_APPROVED.\n"
            f"Causa provável: comparação exata de strings em vez de prefix matching."
        ),
        suggested_fix=fix_code,
        duration_ms=now_ms() - start,
    ))


# ============================================================================
# FASE 5 — VERIFICAÇÃO DO BUG #3 (DISK AUDIT WINDOWS)
# ============================================================================

def check_disk_audit_bug(report: SuperTestReport) -> None:
    """
    BUG #3 — test_report_has_project_data falha porque size_bytes=0 no Windows.
    """
    start = now_ms()

    # Verifica se o arquivo de relatório existe
    report_path = REPO_ROOT / "docs" / "disk_audit_report.json"
    if not report_path.exists():
        report.checks.append(CheckResult(
            "bug_disk_audit_windows", "cosmetic", "skip",
            "disk_audit_report.json não existe — rode 'omnis disk' primeiro",
            duration_ms=now_ms() - start,
        ))
        return

    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
        projects = data.get("project_directories", [])
        omnis = next((p for p in projects if p.get("name") == "omnis-control"), None)
        if omnis is None:
            report.checks.append(CheckResult(
                "bug_disk_audit_windows", "cosmetic", "warn",
                "omnis-control não encontrado no relatório de disco",
                duration_ms=now_ms() - start,
            ))
            return

        size = omnis.get("size_bytes", 0)
        if size == 0:
            fix_code = """
# FIX para BUG #3 (disk audit Windows-specific)
# Localização provável: src/scripts/disk_audit_readonly.py ou src/scripts/diskauditreadonly.py
# Função que calcula tamanho de diretório

# CAUSA: os.walk() bate em pasta protegida (ex: .git/objects, __pycache__) e
#        levanta PermissionError no Windows, retornando size=0.

# ANTES (provável):
def calculate_dir_size(path: Path) -> int:
    total = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            total += (Path(root) / f).stat().st_size
    return total

# DEPOIS (com skip de pastas protegidas + ignore de erros):
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}

def calculate_dir_size(path: Path) -> int:
    total = 0
    for root, dirs, files in os.walk(path, onerror=lambda e: None):
        # Pula pastas problemáticas
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            try:
                total += (Path(root) / f).stat().st_size
            except (PermissionError, FileNotFoundError, OSError):
                continue  # Ignora arquivos inacessíveis
    return total

# Teste após fix:
# python omnis.py disk
# python -m pytest tests/test_disk_audit_readonly.py -v
"""
            report.checks.append(CheckResult(
                "bug_disk_audit_windows", "cosmetic", "warn",
                "size_bytes=0 confirmado para omnis-control",
                details=(
                    f"Plataforma: {platform.system()}\n"
                    f"Esperado: > 0 bytes\n"
                    f"Atual: 0 bytes\n"
                    f"Causa provável: os.walk() bate em pasta protegida (.git/objects, etc.) "
                    f"e levanta PermissionError no Windows."
                ),
                suggested_fix=fix_code,
                duration_ms=now_ms() - start,
            ))
        else:
            report.checks.append(CheckResult(
                "bug_disk_audit_windows", "cosmetic", "ok",
                f"size_bytes={size:,} para omnis-control",
                duration_ms=now_ms() - start,
            ))
    except Exception as e:
        report.checks.append(CheckResult(
            "bug_disk_audit_windows", "cosmetic", "warn",
            f"erro lendo relatório: {e}",
            duration_ms=now_ms() - start,
        ))


# ============================================================================
# FASE 6 — SMOKE TEST END-TO-END (SE POSSÍVEL)
# ============================================================================

def check_pipeline_e2e_smoke(report: SuperTestReport) -> None:
    """
    Tenta rodar pipeline dry-run com um caption aprovado.
    Não corrige nada — só verifica se o sistema consegue gerar um package.
    """
    start = now_ms()

    # Tenta achar uma queue ID com caption aprovado
    rc, out, _ = run_cmd(
        f"{sys.executable} omnis.py captions list",
        timeout=TIMEOUT_SHORT,
    )

    if rc != 0:
        report.checks.append(CheckResult(
            "smoke_pipeline_e2e", "important", "skip",
            "não consegui listar captions",
            duration_ms=now_ms() - start,
        ))
        return

    # Acha primeira linha com 'approved'
    approved_match = None
    for ln in out.splitlines():
        if "approved" in ln.lower() and "│" in ln:
            # Extrai segundo campo (Queue ID)
            parts = [p.strip() for p in ln.split("│") if p.strip()]
            if len(parts) >= 2:
                approved_match = parts[1]  # Queue ID
                break

    if not approved_match:
        report.checks.append(CheckResult(
            "smoke_pipeline_e2e", "important", "skip",
            "nenhum caption aprovado encontrado — não dá pra fazer smoke test",
            duration_ms=now_ms() - start,
        ))
        return

    # Roda pipeline dry-run com ID curto (vai falhar se BUG #1 ativo) e completo
    queue_id_short = approved_match
    rc, out, err = run_cmd(
        f"{sys.executable} omnis.py pipeline dry-run {queue_id_short}",
        timeout=TIMEOUT_SHORT,
    )

    duration = now_ms() - start

    if rc != 0:
        report.checks.append(CheckResult(
            "smoke_pipeline_e2e", "important", "warn",
            f"pipeline dry-run {queue_id_short} → exit code {rc}",
            details=(err + "\n" + out)[-500:],
            duration_ms=duration,
        ))
        return

    # Analisa output
    if "BLOCKED" in out and "CAPTION_NOT_APPROVED" in out:
        report.checks.append(CheckResult(
            "smoke_pipeline_e2e", "important", "warn",
            "pipeline rodou mas BLOQUEOU em CAPTION_NOT_APPROVED",
            details=(
                f"Queue ID usado: {queue_id_short}\n"
                f"Sintoma: BUG #1 (truncamento) confirmado.\n"
                f"Workaround: rodar com ID completo (12+ chars).\n\n"
                f"Output:\n{out[-500:]}"
            ),
            suggested_fix="Aplicar FIX do BUG #1 (prefix matching).",
            duration_ms=duration,
        ))
    elif "BLOCKED" in out:
        report.checks.append(CheckResult(
            "smoke_pipeline_e2e", "important", "warn",
            "pipeline rodou mas BLOQUEOU (motivo diferente de truncamento)",
            details=out[-500:],
            duration_ms=duration,
        ))
    else:
        report.checks.append(CheckResult(
            "smoke_pipeline_e2e", "important", "ok",
            f"pipeline dry-run completou para queue {queue_id_short}",
            details=out[-500:],
            duration_ms=duration,
        ))


# ============================================================================
# FASE 7 — VERIFICAÇÕES DE EVOLUÇÃO (o que falta pra próxima fase)
# ============================================================================

EVOLUTION_CHECKLIST = [
    ("src/mission_contract", "Mission Contract (P0.5)", "Ainda não existe — próxima fase"),
    ("src/task_state", "TaskState durável (P0.5)", "Ainda não existe — próxima fase"),
    ("src/frontend", "Frontend chat-first", "Diretriz fundadora do Lucas — ainda não existe"),
    ("src/sales_lead_registry", "Sales Lead Registry", "Pipeline 150 influenciadores Interior SP"),
    ("src/tool_registry", "Tool/Connector Registry", "Catálogo unificado de tools"),
    ("src/metrics_spine", "Metrics Spine", "5 métricas críticas centralizadas"),
]


def check_evolution_gaps(report: SuperTestReport) -> None:
    """Lista módulos que ainda não existem mas estão no roadmap."""
    for path, name, descr in EVOLUTION_CHECKLIST:
        full_path = REPO_ROOT / path
        if full_path.exists():
            report.checks.append(CheckResult(
                f"evolution_{path.replace('/', '_')}",
                "cosmetic", "ok",
                f"{name} → existe",
                details=f"Path: {path}",
            ))
        else:
            report.checks.append(CheckResult(
                f"evolution_{path.replace('/', '_')}",
                "cosmetic", "warn",
                f"{name} → não existe",
                details=descr,
                suggested_fix=f"Criar módulo na próxima fase.",
            ))


# ============================================================================
# GERADOR DE RELATÓRIO MARKDOWN
# ============================================================================

def generate_report_md(report: SuperTestReport) -> str:
    """Gera o markdown final do relatório."""
    lines = []
    lines.append(f"# OMNIS Super Test — Relatório Diagnostic")
    lines.append("")
    lines.append(f"**Data:** {report.timestamp}")
    lines.append(f"**Duração total:** {report.duration_total_s:.1f}s")
    lines.append(f"**Repo:** {report.repo_root}")
    lines.append(f"**Branch:** `{report.git_branch}`")
    lines.append(f"**Commit:** `{report.git_commit[:80]}`")
    lines.append(f"**Python:** {report.python_version}")
    lines.append(f"**Plataforma:** {report.platform}")
    lines.append("")

    s = report.stats
    total = sum(s.values())
    lines.append(f"## 📊 Resumo executivo")
    lines.append("")
    lines.append(f"- ✅ OK: **{s['ok']}**")
    lines.append(f"- 🟡 Warnings: **{s['warn']}**")
    lines.append(f"- ❌ Failures: **{s['fail']}**")
    lines.append(f"- ⏭️ Skipped: **{s['skip']}**")
    lines.append(f"- **Total:** {total} verificações")
    lines.append("")

    if s['fail'] == 0:
        lines.append("> 🎯 **Sem falhas críticas.** Sistema operacional.")
    else:
        lines.append(f"> ⚠️ **{s['fail']} falhas críticas detectadas.** Revisar abaixo.")
    lines.append("")

    # Agrupar por categoria
    by_category: dict[str, list[CheckResult]] = {"critical": [], "important": [], "cosmetic": []}
    for c in report.checks:
        by_category.setdefault(c.category, []).append(c)

    cat_titles = {
        "critical": "🔴 Críticos (bloqueiam operação)",
        "important": "🟡 Importantes (afetam funcionalidade)",
        "cosmetic": "🟢 Cosméticos (qualidade/futuro)",
    }

    for cat in ["critical", "important", "cosmetic"]:
        checks = by_category[cat]
        if not checks:
            continue
        lines.append(f"## {cat_titles[cat]}")
        lines.append("")
        for c in checks:
            icon = status_icon(c.status)
            lines.append(f"### {icon} `{c.name}` — {c.summary}")
            lines.append("")
            lines.append(f"- **Status:** {c.status.upper()}")
            lines.append(f"- **Duração:** {c.duration_ms}ms")
            if c.details:
                lines.append(f"")
                lines.append(f"<details><summary>Detalhes</summary>")
                lines.append(f"")
                lines.append(f"```")
                lines.append(c.details[:2000])
                lines.append(f"```")
                lines.append(f"</details>")
                lines.append(f"")
            if c.suggested_fix:
                lines.append(f"")
                lines.append(f"<details><summary>💡 Fix sugerido (clique para ver código)</summary>")
                lines.append(f"")
                lines.append(c.suggested_fix)
                lines.append(f"")
                lines.append(f"</details>")
                lines.append(f"")
            lines.append("")

    # Próximas ações sugeridas
    lines.append("## 🎯 Próximas ações sugeridas (em ordem)")
    lines.append("")
    fails = [c for c in report.checks if c.status == "fail"]
    warns = [c for c in report.checks if c.status == "warn"]

    if fails:
        lines.append("### 🔥 Crítico — corrigir AGORA")
        lines.append("")
        for c in fails:
            lines.append(f"1. **{c.name}** → {c.summary}")
        lines.append("")

    if warns:
        lines.append("### 🟡 Médio prazo — aplicar quando tiver tempo")
        lines.append("")
        bug_warnings = [c for c in warns if c.name.startswith("bug_") or c.name == "deprecation_datetime_utcnow"]
        for c in bug_warnings:
            lines.append(f"1. **{c.name}** → {c.summary}")
            if c.suggested_fix:
                lines.append(f"   - Fix sugerido disponível neste relatório (seção acima)")
        lines.append("")

    lines.append("### 🚀 Próxima fase de evolução")
    lines.append("")
    lines.append("- **P0.5** — Mission Contract + TaskState (espinha dorsal Manus-like)")
    lines.append("- **P0.6** — Frontend chat-first (diretriz fundadora)")
    lines.append("- **P0.7** — End-to-end mock com 30 posts (campanha completa simulada)")
    lines.append("- **P0.8** — APENAS DEPOIS, considerar OAuth + 1 publish real")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 🛡️ Notas Feynman — leitura importante")
    lines.append("")
    lines.append("- Este relatório é **diagnostic only**: nada foi modificado no repo.")
    lines.append("- Cada fix sugerido tem **código pronto pra colar** — revise antes de aplicar.")
    lines.append("- Para aplicar um fix: abrir nova conversa em **Sonnet 4.6** (não Opus) com:")
    lines.append("  > `\"Aplicar fix do bug X conforme docs/super_test/<este_relatorio>.md, seção <nome_check>.\"`")
    lines.append("- Volta em Opus apenas para decisões arquiteturais grandes (Mission Contract, OAuth).")
    lines.append("")
    lines.append("**Filosofia:** \"Cada bug é uma decisão consciente do humano.\"")
    lines.append("")
    return "\n".join(lines)


# ============================================================================
# MAIN
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(description="OMNIS Super Test — Diagnostic Only")
    parser.add_argument("--quick", action="store_true", help="Pula testes longos (pytest full)")
    parser.add_argument("--no-cli", action="store_true", help="Pula testes de comandos CLI")
    args = parser.parse_args()

    print("=" * 70)
    print("  OMNIS SUPER TEST — DIAGNOSTIC ONLY")
    print("  Modo 1: identifica problemas, NÃO mexe em nada.")
    print("=" * 70)

    start_total = time.time()
    report = SuperTestReport(timestamp=datetime.now().isoformat())

    # Fase 0
    collect_environment(report)

    # Fase 1
    banner("FASE 1 — Críticos (git/python)")
    check_git_clean(report)
    check_branch_master(report)
    check_python_version(report)

    # Fase 2
    banner("FASE 2 — Suite de testes")
    if args.quick:
        report.checks.append(CheckResult(
            "pytest_suite", "critical", "skip",
            "skipado por --quick",
        ))
        report.checks.append(CheckResult(
            "deprecation_datetime_utcnow", "cosmetic", "skip",
            "skipado por --quick",
        ))
    else:
        check_pytest_full(report)
        check_deprecation_warnings(report)

    # Fase 3
    if not args.no_cli:
        banner("FASE 3 — Comandos CLI (smoke)")
        check_cli_commands(report)

    # Fase 4
    banner("FASE 4 — BUG #1 (truncamento de IDs)")
    check_id_truncation_bug(report)

    # Fase 5
    banner("FASE 5 — BUG #3 (disk audit Windows)")
    check_disk_audit_bug(report)

    # Fase 6
    if not args.no_cli:
        banner("FASE 6 — Smoke test end-to-end")
        check_pipeline_e2e_smoke(report)

    # Fase 7
    banner("FASE 7 — Gaps de evolução (o que falta)")
    check_evolution_gaps(report)

    # Finaliza
    report.duration_total_s = time.time() - start_total

    # Resumo final no terminal
    s = report.stats
    print()
    print("=" * 70)
    print(f"  RESULTADO: ✅ {s['ok']}  🟡 {s['warn']}  ❌ {s['fail']}  ⏭️ {s['skip']}")
    print(f"  Duração: {report.duration_total_s:.1f}s")
    print("=" * 70)

    # Salva relatório
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORT_DIR / f"RELATORIO_{timestamp}.md"
    report_path.write_text(generate_report_md(report), encoding="utf-8")

    print()
    print(f"📋 Relatório completo:")
    print(f"   {report_path}")
    print()
    print("   Abra com:")
    print(f"   notepad {report_path}    (Windows)")
    print(f"   cat '{report_path}'      (PowerShell)")
    print()

    # Sugere próximo passo
    if s['fail'] > 0:
        print("⚠️ Há falhas críticas. Leia o relatório antes de continuar.")
        return 1
    elif s['warn'] > 0:
        print("🟡 Há warnings. Sistema operacional, mas há melhorias sugeridas.")
        return 0
    else:
        print("✅ Tudo verde. Sistema saudável.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
