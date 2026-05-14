"""P29 OMNIS OS Layer — LegacyModule wrapper.

Wraps modules that predate the P29 contract so they can participate
in the OMNIS OS ecosystem without refactoring.
"""
import importlib
from typing import Optional

from src.omnis_os.models import ModuleInfo, ModuleHealth, HEALTH_UNKNOWN, STATUS_REGISTERED
from src.omnis_os.module_contract import OmnisModule


class LegacyModuleWrapper(OmnisModule):
    """Wraps a pre-P29 module into the OmnisModule contract.

    Legacy modules are marked with is_legacy=True and HEALTH_UNKNOWN
    until a manual health_check is performed.
    """

    def __init__(self, module_name: str, namespace: str = "",
                 module_path: str = ""):
        self._name = module_name
        self._namespace = namespace or self._infer_namespace(module_path)
        self._version = "0.0.0"
        self._deps: list[str] = []
        self._module_path = module_path or module_name
        self._imports_ok: Optional[bool] = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def namespace(self) -> str:
        return self._namespace

    @property
    def version(self) -> str:
        return self._version

    @property
    def dependencies(self) -> list[str]:
        return self._deps

    def set_version(self, version: str) -> None:
        self._version = version

    def set_dependencies(self, deps: list[str]) -> None:
        self._deps = deps

    def _infer_namespace(self, module_path: str) -> str:
        if not module_path:
            return "legacy"
        # e.g. "src.old_module" → "src"
        parts = module_path.split(".")
        if len(parts) >= 1:
            return parts[0]
        return "legacy"

    def _probe_import(self) -> bool:
        """Try to import the module. Returns True if successful."""
        if self._imports_ok is not None:
            return self._imports_ok
        try:
            importlib.import_module(self._module_path)
            self._imports_ok = True
        except ImportError:
            self._imports_ok = False
        return self._imports_ok

    def health_check(self) -> ModuleHealth:
        imports_ok = self._probe_import()
        status = HEALTH_UNKNOWN if imports_ok is None else (
            "healthy" if imports_ok else "error"
        )
        return ModuleHealth.new(
            self._name, status=status, imports_ok=imports_ok,
            version=self._version,
            warnings=["Legacy module — no structured tests available"],
        )

    def get_exports(self) -> dict:
        return {"_legacy": True, "name": self._name, "path": self._module_path}

    def to_module_info(self) -> ModuleInfo:
        """Convert this wrapper to a ModuleInfo for the registry."""
        return ModuleInfo(
            module_id=f"om_legacy_{self._name}",
            name=self._name,
            namespace=self._namespace,
            version=self._version,
            status=STATUS_REGISTERED,
            dependencies=self._deps,
            health=self.health_check(),
            is_legacy=True,
        )
