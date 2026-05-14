"""P24 Live Cockpit Supreme — errors."""


class CockpitError(Exception):
    """Base error for P24 Live Cockpit Supreme."""


class ModuleUnreachableError(CockpitError):
    """Modulo nao pode ser importado ou acessado."""


class CollectionError(CockpitError):
    """Falha na coleta de dados de um modulo."""


class RenderError(CockpitError):
    """Falha ao renderizar cockpit."""


class ExportError(CockpitError):
    """Falha ao exportar snapshot."""
