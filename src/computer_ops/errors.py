"""Computer Ops module errors."""


class ComputerOpsError(Exception):
    """Erro base do modulo Computer Ops."""
    pass


class AuditPlanError(ComputerOpsError):
    """Erro ao construir plano de auditoria."""
    pass


class EmptyTargetListError(AuditPlanError):
    """Lista de alvos esta vazia."""
    pass


class InvalidTargetTypeError(AuditPlanError):
    """Tipo de alvo invalido."""
    pass


class ClassificationError(ComputerOpsError):
    """Erro ao classificar candidato a limpeza."""
    pass


class DestructiveActionBlockedError(ClassificationError):
    """Acao destrutiva bloqueada por regra de seguranca."""
    pass


class SafetyViolationError(ComputerOpsError):
    """Violacao de regra de seguranca."""
    pass


class QuarantineRequiredError(SafetyViolationError):
    """Quarentena obrigatoria antes de qualquer delete."""
    pass


class CleanupPlanError(ComputerOpsError):
    """Erro ao gerar plano de limpeza segura."""
    pass


class AlreadyCleanedError(CleanupPlanError):
    """Candidato ja foi processado."""
    pass
