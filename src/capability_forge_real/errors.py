"""P22 Capability Forge Real errors."""


class ForgeRealError(Exception):
    """Base error for P22 Capability Forge Real."""


class BuildError(ForgeRealError):
    """Falha no build de uma capability."""


class ScaffoldError(BuildError):
    """Falha ao gerar scaffold (path ja existe, template invalido)."""


class PolicyScanError(BuildError):
    """Violacao de politica de seguranca no codigo gerado."""


class TestGenerationError(BuildError):
    """Falha ao gerar ou validar testes."""


class RegistrationError(ForgeRealError):
    """Falha ao registrar capability como active."""


class RollbackError(ForgeRealError):
    """Falha no rollback de arquivos gerados."""
