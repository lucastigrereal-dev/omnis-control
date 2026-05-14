"""P29 OMNIS OS Layer — OmnisModule ABC."""
from abc import ABC, abstractmethod

from src.omnis_os.models import ModuleHealth


class OmnisModule(ABC):
    """Abstract base for all OMNIS OS modules.

    Every module must declare its name, namespace, version, and dependencies,
    and implement health_check() and get_exports().
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique module name."""
        ...

    @property
    @abstractmethod
    def namespace(self) -> str:
        """Module namespace (e.g. 'omnis_os', 'self_improvement')."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version string."""
        ...

    @property
    def dependencies(self) -> list[str]:
        """Module names this module depends on."""
        return []

    @abstractmethod
    def health_check(self) -> ModuleHealth:
        """Run self-diagnostics and return health status."""
        ...

    @abstractmethod
    def get_exports(self) -> dict:
        """Return the module's public API mapping."""
        ...
