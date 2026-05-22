"""Policy Engine — AST scanner + regex para skills low-risk."""
from __future__ import annotations
import ast
import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger("omnis.forge.policy")

FORBIDDEN_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"open\s*\(['\"].*\.env"), "Acesso a .env proibido"),
    (re.compile(r"subprocess\.(?:run|call|Popen|check_output)"), "subprocess proibido"),
    (re.compile(r"os\.system\s*\("), "os.system proibido"),
    (re.compile(r"__import__\s*\("), "__import__ dinamico proibido"),
    (re.compile(r"eval\s*\("), "eval() proibido"),
    (re.compile(r"exec\s*\("), "exec() proibido"),
    (re.compile(r"shutil\.rm"), "shutil.rmtree proibido"),
    (re.compile(r"os\.remove|os\.unlink"), "delecao de arquivo proibida"),
    (re.compile(r"requests\.(?:get|post|put|delete|patch)"), "HTTP externo direto — use integrations/"),
    (re.compile(r"DROP\s+TABLE|DELETE\s+FROM|TRUNCATE", re.IGNORECASE), "DDL/DML destrutivo proibido"),
]

FORBIDDEN_IMPORTS = {"subprocess", "socket", "ftplib", "smtplib", "paramiko", "fabric"}


@dataclass
class PolicyViolation:
    line: int
    pattern: str
    description: str


@dataclass
class PolicyReport:
    violations: List[PolicyViolation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.passed:
            return "Policy check passed — nenhuma violacao encontrada."
        lines = ["Policy check FAILED:"]
        for v in self.violations:
            lines.append(f"  Linha {v.line}: {v.description} ({v.pattern})")
        return "\n".join(lines)


class PolicyEngine:
    """Valida run.py contra regras de seguranca."""

    def check_file(self, code_path: Path) -> PolicyReport:
        report = PolicyReport()
        if not code_path.exists():
            report.violations.append(PolicyViolation(0, "file", f"Arquivo nao encontrado: {code_path}"))
            return report

        source = code_path.read_text(encoding="utf-8")
        lines = source.splitlines()

        for i, line in enumerate(lines, 1):
            for pattern, description in FORBIDDEN_PATTERNS:
                if pattern.search(line):
                    report.violations.append(PolicyViolation(i, pattern.pattern, description))

        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    module = getattr(node, "module", "") or ""
                    for alias in getattr(node, "names", []):
                        name = alias.name or ""
                        if name in FORBIDDEN_IMPORTS or module in FORBIDDEN_IMPORTS:
                            report.violations.append(
                                PolicyViolation(node.lineno, name or module, f"Import proibido: {name or module}")
                            )
        except SyntaxError as e:
            report.violations.append(PolicyViolation(0, "syntax", f"Erro de sintaxe: {e}"))

        return report
