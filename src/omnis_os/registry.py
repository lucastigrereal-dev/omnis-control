"""P29 OMNIS OS Layer — ModuleRegistry."""
from typing import Optional

from src.omnis_os.models import ModuleInfo
from src.omnis_os.errors import ModuleNotFoundError


class ModuleRegistry:
    """Central registry of all OMNIS OS modules."""

    def __init__(self):
        self._modules: dict[str, ModuleInfo] = {}
        self._by_name: dict[str, str] = {}  # name → module_id

    # ── CRUD ──────────────────────────────────────────────────────

    def register(self, module: ModuleInfo) -> None:
        self._modules[module.module_id] = module
        self._by_name[module.name] = module.module_id

    def unregister(self, module_id: str) -> None:
        mod = self._modules.pop(module_id, None)
        if mod and mod.name in self._by_name:
            del self._by_name[mod.name]

    def get(self, module_id: str) -> ModuleInfo:
        if module_id not in self._modules:
            raise ModuleNotFoundError(f"Module not found: {module_id}")
        return self._modules[module_id]

    def find(self, name: str) -> ModuleInfo:
        """Find by name. Raises ModuleNotFoundError if not found."""
        module_id = self._by_name.get(name)
        if module_id is None:
            raise ModuleNotFoundError(f"Module not found: {name}")
        return self._modules[module_id]

    def find_by_name(self, name: str) -> Optional[ModuleInfo]:
        """Look up by name. Returns None if not found."""
        module_id = self._by_name.get(name)
        return self._modules.get(module_id) if module_id else None

    # ── Listing ───────────────────────────────────────────────────

    def list_all(self) -> list[ModuleInfo]:
        return list(self._modules.values())

    def list_active(self) -> list[ModuleInfo]:
        from src.omnis_os.models import STATUS_ACTIVE
        return [m for m in self._modules.values() if m.status == STATUS_ACTIVE]

    def list_by_namespace(self, namespace: str) -> list[ModuleInfo]:
        return [m for m in self._modules.values() if m.namespace == namespace]

    def list_legacy(self) -> list[ModuleInfo]:
        return [m for m in self._modules.values() if m.is_legacy]

    # ── Lookup helpers ────────────────────────────────────────────

    def resolve(self, ref: str) -> ModuleInfo:
        """Try by ID first, then by name. Raises ModuleNotFoundError."""
        try:
            return self.get(ref)
        except ModuleNotFoundError:
            return self.find(ref)

    def exists(self, name: str) -> bool:
        return name in self._by_name

    # ── Info ──────────────────────────────────────────────────────

    @property
    def module_count(self) -> int:
        return len(self._modules)

    @property
    def module_names(self) -> list[str]:
        return list(self._by_name.keys())
