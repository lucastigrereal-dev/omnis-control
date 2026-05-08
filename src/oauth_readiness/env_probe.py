"""Safe .env probe — detecta presenca de variaveis sem ler valores.

NUNCA armazena, retorna ou imprime valores de segredo.
Apenas classifica cada variavel como: present, missing, empty, invalid_format.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class EnvVarStatus:
    PRESENT = "present"
    MISSING = "missing"
    EMPTY = "empty"
    INVALID_FORMAT = "invalid_format"
    ALIAS_PRESENT = "alias_present"


@dataclass
class EnvProbeResult:
    var_name: str
    canonical_name: str
    status: str
    required: bool = True
    found_via_alias: Optional[str] = None
    format_note: str = ""

    def __repr__(self) -> str:
        return f"EnvProbeResult({self.var_name}={self.status})"

    def __str__(self) -> str:
        return f"{self.var_name}: {self.status}"


@dataclass
class EnvProbeSummary:
    results: List[EnvProbeResult] = field(default_factory=list)
    source_path: str = ""
    file_exists: bool = False

    @property
    def present_count(self) -> int:
        return sum(1 for r in self.results if r.status == EnvVarStatus.PRESENT)

    @property
    def missing_count(self) -> int:
        return sum(1 for r in self.results if r.status == EnvVarStatus.MISSING)

    @property
    def empty_count(self) -> int:
        return sum(1 for r in self.results if r.status == EnvVarStatus.EMPTY)

    @property
    def invalid_count(self) -> int:
        return sum(1 for r in self.results if r.status == EnvVarStatus.INVALID_FORMAT)

    @property
    def alias_count(self) -> int:
        return sum(1 for r in self.results if r.status == EnvVarStatus.ALIAS_PRESENT)

    @property
    def total_checked(self) -> int:
        return len(self.results)

    @property
    def all_required_present(self) -> bool:
        required = [r for r in self.results if r.required]
        return all(r.status == EnvVarStatus.PRESENT for r in required)

    def to_dict(self) -> dict:
        """Retorna dicionario SEGURO — apenas status, nunca valores."""
        return {
            "source_path": self.source_path,
            "file_exists": self.file_exists,
            "total_checked": self.total_checked,
            "present_count": self.present_count,
            "missing_count": self.missing_count,
            "empty_count": self.empty_count,
            "invalid_count": self.invalid_count,
            "all_required_present": self.all_required_present,
            "variables": [
                {
                    "var_name": r.var_name,
                    "canonical_name": r.canonical_name,
                    "status": r.status,
                    "required": r.required,
                    "found_via_alias": r.found_via_alias,
                    "format_note": r.format_note,
                }
                for r in self.results
            ],
        }

    def __repr__(self) -> str:
        return f"EnvProbeSummary({self.total_checked} vars, {self.present_count} present, source={self.source_path})"


DEFAULT_META_VARS: Dict[str, dict] = {
    "META_APP_ID": {
        "required": True,
        "validate": "numeric",
        "aliases": [],
    },
    "META_APP_SECRET": {
        "required": True,
        "validate": "non_empty",
        "aliases": ["META_SECRET"],
    },
    "META_REDIRECT_URI": {
        "required": True,
        "validate": "url",
        "aliases": ["CALLBACK_URL", "REDIRECT_URI"],
    },
    "META_GRAPH_VERSION": {
        "required": True,
        "validate": "graph_version",
        "aliases": [],
    },
    "INSTAGRAM_BUSINESS_ACCOUNT_ID": {
        "required": False,
        "validate": "numeric_or_empty",
        "aliases": ["INSTAGRAM_BUSINESS_ID", "INSTAGRAM_BUSINESS_ACCOUNT"],
    },
    "FACEBOOK_PAGE_ID": {
        "required": False,
        "validate": "numeric_or_empty",
        "aliases": ["FB_PAGE_ID"],
    },
    "META_ACCESS_TOKEN": {
        "required": False,
        "validate": "non_empty_or_missing",
        "aliases": ["ACCESS_TOKEN", "META_TOKEN"],
    },
}


def _read_env_file(path: str) -> Dict[str, str]:
    """Le um arquivo .env e retorna dict KEY->VALUE.

    ATENCAO: Esta funcao e interna. Nunca retorne o dict para fora
    do modulo. Use apenas para classificar status.
    """
    if not os.path.isfile(path):
        return {}

    result: Dict[str, str] = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                if value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                result[key] = value
    except OSError:
        pass
    return result


def _validate_format(value: str, rule: str) -> tuple[bool, str]:
    """Valida formato do valor contra regra. Retorna (ok, note)."""
    if rule == "non_empty":
        return len(value) > 0, ""
    if rule == "numeric":
        ok = bool(re.match(r"^\d+$", value))
        return ok, "" if ok else "deve ser numerico"
    if rule == "url":
        ok = bool(re.match(r"^https?://", value))
        return ok, "" if ok else "deve comecar com http:// ou https://"
    if rule == "graph_version":
        ok = bool(re.match(r"^v\d+\.\d+$", value))
        return ok, "" if ok else "formato esperado: vXX.Y (ex: v20.0)"
    if rule == "numeric_or_empty":
        if len(value) == 0:
            return True, ""
        ok = bool(re.match(r"^\d+$", value))
        return ok, "" if ok else "se preenchido, deve ser numerico"
    if rule == "non_empty_or_missing":
        return True, ""
    return True, ""


def probe_env_vars(
    path: str,
    expected_vars: Optional[Dict[str, dict]] = None,
) -> EnvProbeSummary:
    """Verifica variaveis esperadas em arquivo .env.

    Retorna EnvProbeSummary com status de cada variavel.
    NUNCA inclui valores no resultado.

    Args:
        path: Caminho para o arquivo .env
        expected_vars: Dict de vars esperadas {NOME: {required, validate, aliases}}
                       Se None, usa DEFAULT_META_VARS
    """
    if expected_vars is None:
        expected_vars = DEFAULT_META_VARS

    file_exists = os.path.isfile(path)
    if not file_exists:
        results = [
            EnvProbeResult(
                var_name=name,
                canonical_name=name,
                status=EnvVarStatus.MISSING,
                required=cfg.get("required", True),
            )
            for name, cfg in expected_vars.items()
        ]
        return EnvProbeSummary(results=results, source_path=path, file_exists=False)

    raw = _read_env_file(path)
    results: List[EnvProbeResult] = []

    for canonical_name, cfg in expected_vars.items():
        required = cfg.get("required", True)
        aliases: List[str] = cfg.get("aliases", [])
        validate_rule: str = cfg.get("validate", "non_empty")

        # 1. Buscar nome canonico
        if canonical_name in raw:
            value = raw[canonical_name]
            _classify_value(results, canonical_name, canonical_name, value, validate_rule, required)
            continue

        # 2. Buscar aliases
        found_alias = None
        for alias in aliases:
            if alias in raw:
                found_alias = alias
                break

        if found_alias:
            value = raw[found_alias]
            result = EnvProbeResult(
                var_name=found_alias,
                canonical_name=canonical_name,
                status=EnvVarStatus.ALIAS_PRESENT,
                required=required,
                found_via_alias=found_alias,
                format_note=f"Use nome canonico: {canonical_name}",
            )
            # Validar formato mesmo via alias
            if len(value) == 0:
                result.status = EnvVarStatus.EMPTY
            else:
                fmt_ok, fmt_note = _validate_format(value, validate_rule)
                if not fmt_ok:
                    result.status = EnvVarStatus.INVALID_FORMAT
                    result.format_note = f"{result.format_note}; {fmt_note}"
            results.append(result)
            continue

        # 3. Nao encontrada
        results.append(EnvProbeResult(
            var_name=canonical_name,
            canonical_name=canonical_name,
            status=EnvVarStatus.MISSING,
            required=required,
        ))

    return EnvProbeSummary(results=results, source_path=path, file_exists=True)


def _classify_value(
    results: List[EnvProbeResult],
    var_name: str,
    canonical_name: str,
    value: str,
    validate_rule: str,
    required: bool,
) -> None:
    """Classifica o valor e adiciona a results. Valor nunca sai deste escopo."""
    if len(value) == 0:
        results.append(EnvProbeResult(
            var_name=var_name,
            canonical_name=canonical_name,
            status=EnvVarStatus.EMPTY,
            required=required,
        ))
        return

    fmt_ok, fmt_note = _validate_format(value, validate_rule)
    if not fmt_ok:
        results.append(EnvProbeResult(
            var_name=var_name,
            canonical_name=canonical_name,
            status=EnvVarStatus.INVALID_FORMAT,
            required=required,
            format_note=fmt_note,
        ))
        return

    results.append(EnvProbeResult(
        var_name=var_name,
        canonical_name=canonical_name,
        status=EnvVarStatus.PRESENT,
        required=required,
    ))


def safe_summary(probe: EnvProbeSummary) -> str:
    """Gera resumo seguro para consumo humano — sem valores."""
    if not probe.file_exists:
        return f"Arquivo .env nao encontrado: {probe.source_path}"

    lines = [f"Env file: {probe.source_path}"]
    lines.append(f"Variaveis: {probe.total_checked} esperadas, "
                 f"{probe.present_count} presentes, "
                 f"{probe.missing_count} ausentes, "
                 f"{probe.empty_count} vazias, "
                 f"{probe.invalid_count} formato invalido")

    for r in probe.results:
        icon = {
            EnvVarStatus.PRESENT: "[OK]",
            EnvVarStatus.MISSING: "[--]",
            EnvVarStatus.EMPTY: "[??]",
            EnvVarStatus.INVALID_FORMAT: "[!!]",
            EnvVarStatus.ALIAS_PRESENT: "[~A]",
        }.get(r.status, "[?]")
        note = f" — {r.format_note}" if r.format_note else ""
        required_tag = " (obrigatorio)" if r.required else ""
        lines.append(f"  {icon} {r.var_name}: {r.status}{required_tag}{note}")

    return "\n".join(lines)
