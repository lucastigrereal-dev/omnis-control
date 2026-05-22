"""P22 Capability Forge Real — CapabilityBuilder: build skills from approved proposals."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from src.capability_forge_real.models import (
    CapabilityProposal,
    PROPOSAL_STATUS_APPROVED,
    IMPL_TYPE_CLI_WRAPPER,
    IMPL_TYPE_OFFLINE_PACKAGE,
)
from src.capability_forge_real.registrar import register_capability
from src.capability_forge_real.store import ProposalStore
from src.capability_forge_real import store as store_mod
from src.capability_forge_real.models import (
    BuildResult,
    BuildState,
    SkillTemplateConfig,
)
from src.capability_forge_real.scaffold import (
    render_template,
    get_template,
    get_template_config,
    get_file_paths,
    _slug,
)
from src.capability_forge_real.policy_scanner import scan_code
from src.capability_forge_real.test_generator import generate_test_content, count_test_functions
from src.capability_forge_real.errors import (
    ForgeRealError,
    BuildError,
    ScaffoldError,
    PolicyScanError,
    TestGenerationError,
    RegistrationError,
    RollbackError,
)


class CapabilityBuilder:
    """Gera codigo para uma capability aprovada.

    Uso:
        builder = CapabilityBuilder(dry_run=True)
        result = builder.build(proposal)
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.store = ProposalStore(store_mod.DEFAULT_PROPOSALS_LOG)

    def build(self, proposal: CapabilityProposal) -> BuildResult:
        """Pipeline completo: scaffold → scan → test → validate → register.

        Args:
            proposal: CapabilityProposal aprovada

        Returns:
            BuildResult com estado final
        """
        if proposal.status != PROPOSAL_STATUS_APPROVED:
            raise BuildError(
                f"Proposal {proposal.proposal_id} nao esta aprovada (status={proposal.status})"
            )

        result = BuildResult.new(proposal, dry_run=self.dry_run)

        # Step 1: Scaffold
        files = self.scaffold(proposal)
        result.files_created = [str(f) for f in files]
        result.transition(BuildState.SCAFFOLDING)

        # Step 2: Policy scan (only for code types)
        if proposal.implementation_type in {IMPL_TYPE_CLI_WRAPPER, IMPL_TYPE_OFFLINE_PACKAGE}:
            result.transition(BuildState.POLICY_SCANNING)
            source_template = get_template(proposal.implementation_type)
            if source_template:
                code = render_template(source_template, proposal)
                scan_result = scan_code(code)
                result.policy_scan = scan_result
                if not scan_result["passed"]:
                    result.transition(BuildState.POLICY_FAILED)
                    if not self.dry_run:
                        self.rollback(result.build_id)
                    return result

        # Step 3: Generate tests (only for code types)
        if proposal.implementation_type in {IMPL_TYPE_CLI_WRAPPER, IMPL_TYPE_OFFLINE_PACKAGE}:
            result.transition(BuildState.TEST_GENERATING)
            test_content = generate_test_content(proposal)
            result.test_count = count_test_functions(test_content)

            # Step 4: Validate (min tests check)
            result.transition(BuildState.VALIDATING)
            config = get_template_config(proposal.implementation_type)
            if config and result.test_count < config.min_tests:
                result.transition(BuildState.TEST_FAILED)
                if not self.dry_run:
                    self.rollback(result.build_id)
                return result

        # Step 5: Write files if not dry_run
        if not self.dry_run:
            try:
                self._write_files(proposal)
            except Exception as e:
                self.rollback(result.build_id)
                raise BuildError(f"Falha ao escrever arquivos: {e}") from e

        # Step 6: Register
        result.transition(BuildState.REGISTERING)
        try:
            if not self.dry_run:
                register_capability(proposal.proposal_id, proposals_log=store_mod.DEFAULT_PROPOSALS_LOG)
        except Exception as e:
            raise RegistrationError(f"Falha ao registrar capability: {e}") from e

        result.transition(BuildState.DONE)
        return result

    def scaffold(self, proposal: CapabilityProposal) -> list[Path]:
        """Gera arquivos fonte baseado no implementation_type.

        Args:
            proposal: CapabilityProposal aprovada

        Returns:
            Lista de paths que seriam/serão criados
        """
        template = get_template(proposal.implementation_type)
        if not template:
            raise ScaffoldError(
                f"Template nao encontrado para implementation_type={proposal.implementation_type!r}"
            )

        rendered = render_template(template, proposal)
        paths = get_file_paths(proposal, base_dir=self.base_dir)

        result = []
        for key in ["source", "test"]:
            p = paths.get(key)
            if p and key == "source":
                result.append(p)
            elif p and key == "test":
                result.append(p)

        if not self.dry_run:
            for file_path in result:
                if file_path.exists():
                    raise ScaffoldError(
                        f"Arquivo ja existe: {file_path}. Use outro nome ou remova o existente."
                    )
                file_path.parent.mkdir(parents=True, exist_ok=True)
                if file_path.name.endswith(".py"):
                    file_path.write_text(rendered, encoding="utf-8")
                else:
                    file_path.write_text(rendered, encoding="utf-8")

        return result

    def rollback(self, build_id: str) -> None:
        """Remove arquivos gerados em caso de falha.

        Args:
            build_id: ID do build (nao usado diretamente, remove por paths conhecidos)
        """
        # Rollback is best-effort: delete files that were created
        # Since we track files_created in BuildResult, we'd use that
        # For now, this is a safety placeholder
        pass

    def rollback_files(self, files: list[str]) -> None:
        """Remove arquivos especificos.

        Args:
            files: Lista de paths para remover
        """
        for f in files:
            p = Path(f)
            if p.exists():
                p.unlink()
                # Remove parent dir if empty
                try:
                    p.parent.rmdir()
                except OSError:
                    pass  # dir not empty

    def _write_files(self, proposal: CapabilityProposal) -> None:
        """Escreve arquivos em disco (apenas quando dry_run=False)."""
        template = get_template(proposal.implementation_type)
        if not template:
            return

        rendered = render_template(template, proposal)
        paths = get_file_paths(proposal, base_dir=self.base_dir)

        source_path = paths.get("source")
        if source_path:
            if source_path.exists():
                raise ScaffoldError(f"Arquivo ja existe: {source_path}")
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_text(rendered, encoding="utf-8")

        test_path = paths.get("test")
        if test_path and proposal.implementation_type in {IMPL_TYPE_CLI_WRAPPER, IMPL_TYPE_OFFLINE_PACKAGE}:
            if test_path.exists():
                raise ScaffoldError(f"Arquivo de teste ja existe: {test_path}")
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_content = generate_test_content(proposal)
            test_path.write_text(test_content, encoding="utf-8")
