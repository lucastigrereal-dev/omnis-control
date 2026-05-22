"""Capability Forge Real — merged capability pipeline (proposal → build → register)."""
from src.capability_forge_real.models import (
    CapabilityProposal,
    BuildResult,
    BuildState,
    SkillTemplateConfig,
    CreationContext,
    CreationState,
    SkillSpec,
    RegistryEntry,
    SkillManifest,
    TERMINAL_STATES,
    _new_id,
    _now_iso,
)
from src.capability_forge_real.errors import (
    ForgeRealError,
    BuildError,
    ScaffoldError,
    PolicyScanError,
    TestGenerationError,
    RegistrationError,
    RollbackError,
)
from src.capability_forge_real.builder import CapabilityBuilder
from src.capability_forge_real.lifecycle import transition, InvalidCreationTransitionError
from src.capability_forge_real.policy import PolicyEngine, PolicyReport
from src.capability_forge_real.registrymanager import RegistryManager
from src.capability_forge_real.orchestrator import CapabilityForge
from src.capability_forge_real.policy_scanner import scan_code
from src.capability_forge_real.test_generator import generate_test_content, count_test_functions
from src.capability_forge_real.scaffold import (
    render_template,
    get_template,
    get_template_config,
    get_file_paths,
    SKILL_TEMPLATE,
    OFFLINE_PACKAGE_TEMPLATE,
    MANUAL_PROCESS_TEMPLATE,
    EXTERNAL_FUTURE_TEMPLATE,
    APP_FACTORY_FUTURE_TEMPLATE,
    TEMPLATES,
    TEMPLATE_CONFIGS,
    _slug,
    _class_name,
)
