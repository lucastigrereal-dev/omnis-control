"""P22 Capability Forge Real — code generation from approved proposals."""
from src.capability_forge_real.models import (
    BuildResult,
    BuildState,
    SkillTemplateConfig,
    TERMINAL_STATES,
)
from src.capability_forge_real.builder import CapabilityBuilder
from src.capability_forge_real.scaffold import (
    render_template,
    get_template,
    get_template_config,
    SKILL_TEMPLATE,
    TEMPLATES,
    TEMPLATE_CONFIGS,
)
from src.capability_forge_real.policy_scanner import scan_code, scan_file
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

__all__ = [
    # Models
    "BuildResult",
    "BuildState",
    "SkillTemplateConfig",
    "TERMINAL_STATES",
    # Builder
    "CapabilityBuilder",
    # Scaffold
    "render_template",
    "get_template",
    "get_template_config",
    "SKILL_TEMPLATE",
    "TEMPLATES",
    "TEMPLATE_CONFIGS",
    # Scanner
    "scan_code",
    "scan_file",
    # Test Gen
    "generate_test_content",
    "count_test_functions",
    # Errors
    "ForgeRealError",
    "BuildError",
    "ScaffoldError",
    "PolicyScanError",
    "TestGenerationError",
    "RegistrationError",
    "RollbackError",
]
