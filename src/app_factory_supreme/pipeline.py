"""P26 BuildPipeline — orchestrates the full app build flow."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.app_factory_supreme.code_generator import CodeGenerator
from src.app_factory_supreme.errors import (
    BlueprintNotApprovedError,
    BuildError,
    SecurityScanFailedError,
)
from src.app_factory_supreme.models import (
    BUILD_BLUEPRINTING,
    BUILD_COMPLETE,
    BUILD_FAILED,
    BUILD_GENERATING,
    BUILD_PACKAGING,
    BUILD_PLANNED,
    BUILD_SCANNING,
    BUILD_TESTING,
    AppBuild,
    ModuleBuild,
)
from src.app_factory_supreme.packager import AppPackager
from src.app_factory_supreme.verifier import BuildVerifier

_DEFAULT_OUTPUT_BASE = Path("generated_apps")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class BuildPipeline:
    """Orchestrator: Idea → Blueprint → Code → Tests → Scan → Package."""

    def __init__(
        self,
        dry_run: bool = True,
        output_base: Optional[Path] = None,
    ) -> None:
        self.dry_run = dry_run
        self.output_base = output_base or _DEFAULT_OUTPUT_BASE
        self.code_generator = CodeGenerator(dry_run=dry_run)
        self.verifier = BuildVerifier(dry_run=dry_run)
        self.packager = AppPackager(dry_run=dry_run)

    # ── Public API ─────────────────────────────────────────────────────────

    def build(self, idea: Optional[dict] = None, title: str = "", description: str = "") -> AppBuild:
        """Run the full build pipeline from an idea."""
        build = AppBuild.new(title=title)
        build.status = BUILD_PLANNED

        if idea:
            build.idea_id = idea.get("idea_id", "")

        if self.dry_run:
            return self._build_dry(build, idea)

        return self._build_real(build, idea)

    def plan(self, title: str = "", description: str = "") -> AppBuild:
        """Plan only — no code generation."""
        build = AppBuild.new(title=title)
        build.status = BUILD_BLUEPRINTING

        # Simulate module planning
        modules = self._plan_modules(title, description or "")
        build.modules = [ModuleBuild.new(m) for m in modules]

        build.blueprint_approved = False  # always requires approval
        return build

    def rollback(self, build: AppBuild) -> bool:
        """Rollback a build by marking it as rolled_back."""
        if build.is_terminal:
            return False
        build.status = "rolled_back"
        build.completed_at = _now_iso()
        return True

    # ── Internal ────────────────────────────────────────────────────────────

    def _build_dry(self, build: AppBuild, idea: Optional[dict]) -> AppBuild:
        """Dry-run: plan only, no writes to disk."""
        build.status = BUILD_BLUEPRINTING

        modules = self._plan_modules(build.title, (idea or {}).get("description", ""))
        build.modules = [ModuleBuild.new(m) for m in modules]

        build.blueprint_approved = False
        build.status = BUILD_PLANNED
        build.output_dir = str(self.output_base / "dry_run" / build.build_id)
        return build

    def _build_real(self, build: AppBuild, idea: Optional[dict]) -> AppBuild:
        """Real build with code generation (still requires approval gates)."""
        if not build.blueprint_approved:
            raise BlueprintNotApprovedError("Blueprint must be approved before generating code")

        build.status = BUILD_GENERATING
        for module in build.modules:
            try:
                result = self.code_generator.generate_module(module)
                module.build_result_id = result.get("build_id", "")
                module.status = BUILD_GENERATING
            except Exception as e:
                module.errors.append(str(e)[:200])

        build.status = BUILD_TESTING
        build = self.verifier.verify(build)

        build.status = BUILD_SCANNING
        if not build.security_approved:
            violations = [v for v in build.policy_violations if v.get("severity") in ("critical", "high")]
            if violations:
                raise SecurityScanFailedError(f"Security scan found {len(violations)} critical/high violations")

        build.status = BUILD_PACKAGING
        build = self.packager.package(build)

        build.status = BUILD_COMPLETE
        build.completed_at = _now_iso()
        return build

    @staticmethod
    def _plan_modules(title: str, description: str) -> list[str]:
        """Deterministic module planning from title/description keywords."""
        combined = f"{title} {description}".lower()
        modules = ["core", "tests"]

        if any(kw in combined for kw in ["auth", "login", "user", "usuario"]):
            modules.append("auth")

        if any(kw in combined for kw in ["api", "rest", "endpoint"]):
            modules.append("api")
        elif any(kw in combined for kw in ["web", "site", "page", "pagina", "dashboard"]):
            modules.append("web")

        if any(kw in combined for kw in ["crud", "admin", "manage", "gerenci"]):
            modules.extend(["crud", "admin"])

        if any(kw in combined for kw in ["search", "busca"]):
            modules.append("search")

        if any(kw in combined for kw in ["email", "notif", "alert"]):
            modules.append("notifications")

        if any(kw in combined for kw in ["payment", "pagamento", "billing"]):
            modules.append("payments")

        return modules
