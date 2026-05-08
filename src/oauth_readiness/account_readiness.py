"""Account OAuth Readiness — avalia prontidao de cada conta para OAuth/publicacao.

NUNCA armazena, retorna ou imprime valores de segredo.
Avalia apenas status de configuracao por conta.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AccountRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReadinessStatus(str, Enum):
    READY = "ready"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    HUMAN_REQUIRED = "human_required"
    NOT_CONFIGURED = "not_configured"


# Handles conhecidos com follower counts do CLAUDE.md
KNOWN_HANDLES: dict[str, dict] = {
    "lucastigrereal": {"followers": 690_000, "risk": AccountRisk.CRITICAL, "niche": "Autoridade, lifestyle"},
    "oinatalrn": {"followers": 630_000, "risk": AccountRisk.HIGH, "niche": "Turismo Natal/RN"},
    "agenteviajabrasil": {"followers": 452_000, "risk": AccountRisk.HIGH, "niche": "Viagens Brasil"},
    "afamiliatigrereal": {"followers": 320_000, "risk": AccountRisk.MEDIUM, "niche": "Familia"},
    "oquecomernatalrn": {"followers": 249_000, "risk": AccountRisk.MEDIUM, "niche": "Gastronomia Natal"},
    "natalaivoueu": {"followers": 240_000, "risk": AccountRisk.MEDIUM, "niche": "Guia Natal, praias"},
}

CRITICAL_BLOCKED_HANDLES = {"lucastigrereal"}


class AccountOAuthReadiness(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_handle: str
    account_registry_id: str | None = None
    risk_level: AccountRisk
    is_test_candidate: bool = False

    instagram_business_account_id_status: str = "not_configured"
    facebook_page_id_status: str = "not_configured"
    meta_app_secret_status: str = "not_configured"
    meta_graph_version_status: str = "not_configured"
    callback_status: str = "not_configured"
    token_status: str = "not_configured"

    asset_candidate_status: str = "not_configured"
    caption_candidate_status: str = "not_configured"

    ready_for_oauth: bool = False
    ready_for_first_post: bool = False

    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)

    def safe_summary(self) -> str:
        lines = [
            f"Account: {self.account_handle}",
            f"Risk: {self.risk_level.value}",
            f"Test Candidate: {self.is_test_candidate}",
            f"OAuth Ready: {self.ready_for_oauth}",
            f"First Post Ready: {self.ready_for_first_post}",
        ]
        if self.blockers:
            lines.append(f"Blockers ({len(self.blockers)}):")
            for b in self.blockers:
                lines.append(f"  - {b}")
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"  - {w}")
        if self.next_actions:
            lines.append("Next actions:")
            for a in self.next_actions:
                lines.append(f"  - {a}")
        return "\n".join(lines)


def normalize_handle(handle: str) -> str:
    return handle.strip().lstrip("@").lower()


def risk_for_handle(handle: str, followers: int | None = None) -> AccountRisk:
    norm = normalize_handle(handle)
    if norm in KNOWN_HANDLES:
        return KNOWN_HANDLES[norm]["risk"]
    if followers is not None:
        if followers > 500_000:
            return AccountRisk.CRITICAL
        if followers > 300_000:
            return AccountRisk.HIGH
        if followers > 100_000:
            return AccountRisk.MEDIUM
        return AccountRisk.LOW
    return AccountRisk.MEDIUM


def is_allowed_first_test(handle: str, risk_level: AccountRisk | None = None) -> bool:
    norm = normalize_handle(handle)
    if norm in CRITICAL_BLOCKED_HANDLES:
        return False
    if risk_level is None:
        risk_level = risk_for_handle(handle)
    return risk_level != AccountRisk.CRITICAL


def status_from_env_probe(probe_status: str) -> str:
    mapping = {
        "present": "present",
        "missing": "missing",
        "empty": "empty",
        "alias_present": "alias_present",
        "invalid_format": "invalid_format",
    }
    return mapping.get(probe_status, "not_configured")


def build_account_readiness(
    handle: str,
    account_registry_id: str | None = None,
    env_probe_results: dict[str, str] | None = None,
    has_asset: bool = False,
    has_caption: bool = False,
    callback_http_200: bool = False,
) -> AccountOAuthReadiness:
    norm = normalize_handle(handle)
    risk = risk_for_handle(norm)
    is_test = is_allowed_first_test(norm, risk)

    if env_probe_results is None:
        env_probe_results = {}

    biz_status = env_probe_results.get("INSTAGRAM_BUSINESS_ACCOUNT_ID", "not_configured")
    page_status = env_probe_results.get("FACEBOOK_PAGE_ID", "not_configured")
    secret_status = env_probe_results.get("META_APP_SECRET", "not_configured")
    graph_status = env_probe_results.get("META_GRAPH_VERSION", "not_configured")
    token_status = env_probe_results.get("META_ACCESS_TOKEN", "not_configured")

    callback_status = "present" if callback_http_200 else "not_configured"
    asset_status = "present" if has_asset else "missing"
    caption_status = "present" if has_caption else "missing"

    blockers: list[str] = []
    warnings: list[str] = []
    next_actions: list[str] = []

    if risk == AccountRisk.CRITICAL:
        blockers.append(f"Conta {handle} e de risco CRITICO — nao pode ser primeiro teste")
    if risk == AccountRisk.HIGH:
        warnings.append(f"Conta {handle} e de risco HIGH — nao recomendada para primeiro teste")

    if biz_status in ("missing", "empty", "not_configured"):
        blockers.append("INSTAGRAM_BUSINESS_ACCOUNT_ID ausente ou vazio")
    if page_status in ("missing", "not_configured"):
        warnings.append("FACEBOOK_PAGE_ID ausente — recomendado preencher")
    if secret_status in ("empty", "missing", "not_configured"):
        blockers.append("META_APP_SECRET nao configurado")
    if graph_status in ("missing", "not_configured"):
        blockers.append("META_GRAPH_VERSION ausente")
    if token_status in ("missing", "not_configured"):
        warnings.append("META_ACCESS_TOKEN ausente — sera obtido no OAuth")

    if not has_asset:
        warnings.append("Nenhum asset atribuido — necessario para publicacao")
    if not has_caption:
        warnings.append("Nenhuma caption pronta — necessario para publicacao")

    ready_oauth = len([b for b in blockers if "primeiro teste" not in b and "CRITICO" not in b]) == 0
    ready_first_post = ready_oauth and has_asset and has_caption and risk != AccountRisk.CRITICAL

    if biz_status in ("missing", "empty", "not_configured"):
        next_actions.append("Preencher INSTAGRAM_BUSINESS_ACCOUNT_ID no .env")
    if secret_status in ("empty", "missing", "not_configured"):
        next_actions.append("Preencher META_APP_SECRET no .env")
    if graph_status in ("missing", "not_configured"):
        next_actions.append("Adicionar META_GRAPH_VERSION=v20.0 ao .env")
    if not has_asset:
        next_actions.append("Atribuir asset ao slot via: python jarvis.py queue assign <queue_id> <asset_id>")

    return AccountOAuthReadiness(
        account_handle=handle,
        account_registry_id=account_registry_id,
        risk_level=risk,
        is_test_candidate=is_test,
        instagram_business_account_id_status=biz_status,
        facebook_page_id_status=page_status,
        meta_app_secret_status=secret_status,
        meta_graph_version_status=graph_status,
        callback_status=callback_status,
        token_status=token_status,
        asset_candidate_status=asset_status,
        caption_candidate_status=caption_status,
        ready_for_oauth=ready_oauth,
        ready_for_first_post=ready_first_post,
        blockers=blockers,
        warnings=warnings,
        next_actions=next_actions,
    )


def build_accounts_readiness(
    handles: list[str],
    env_probe_results: dict[str, str] | None = None,
    account_assets: dict[str, bool] | None = None,
    account_captions: dict[str, bool] | None = None,
    callback_http_200: bool = False,
) -> list[AccountOAuthReadiness]:
    if account_assets is None:
        account_assets = {}
    if account_captions is None:
        account_captions = {}
    results: list[AccountOAuthReadiness] = []
    for handle in handles:
        results.append(
            build_account_readiness(
                handle=handle,
                env_probe_results=env_probe_results,
                has_asset=account_assets.get(normalize_handle(handle), False),
                has_caption=account_captions.get(normalize_handle(handle), False),
                callback_http_200=callback_http_200,
            )
        )
    return results
