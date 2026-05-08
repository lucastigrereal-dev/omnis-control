"""OAuth Readiness errors — P1.2a."""


class OAuthReadinessError(Exception):
    """Erro base do OAuth Readiness module."""


class CheckExecutionError(OAuthReadinessError):
    """Falha ao executar um check individual."""


class ReadinessNotSatisfiedError(OAuthReadinessError):
    """Precondicoes nao atendidas — bloqueio antes de iniciar OAuth."""
