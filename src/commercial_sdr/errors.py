"""Commercial SDR module errors."""


class CommercialSDRError(Exception):
    """Erro base do modulo Commercial SDR."""
    pass


class InvalidProspectError(CommercialSDRError):
    """Perfil de prospect invalido."""
    pass


class EmptyProspectListError(CommercialSDRError):
    """Lista de prospects esta vazia."""
    pass


class ScoringError(CommercialSDRError):
    """Erro ao calcular score de oportunidade."""
    pass


class InvalidScoreParameterError(ScoringError):
    """Parametro de score fora do intervalo [0.0, 1.0]."""
    pass


class SequenceBuildError(CommercialSDRError):
    """Erro ao construir sequencia de outreach."""
    pass


class InvalidChannelError(SequenceBuildError):
    """Canal de outreach invalido para a operacao."""
    pass


class MessageTemplateError(CommercialSDRError):
    """Erro ao gerar mensagem de outreach."""
    pass


class ApprovalRequiredError(CommercialSDRError):
    """Acao requer aprovacao humana antes de executar."""
    pass


class RiskBlockedError(CommercialSDRError):
    """Acao bloqueada por flag de risco ativa."""
    pass


class DryRunViolationError(CommercialSDRError):
    """Tentativa de executar envio real em modo dry-run."""
    pass


class ValidationError(CommercialSDRError):
    """Erro de validacao de sequencia."""
    pass


class PlanFinalizedError(CommercialSDRError):
    """Operacao bloqueada — plano ja foi finalizado."""
    pass
