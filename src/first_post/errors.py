"""First Post Preflight errors — P1.3a."""


class FirstPostError(Exception):
    """Erro base do First Post module."""


class PreflightFailedError(FirstPostError):
    """Preflight checks falharam — bloqueio antes de publicar."""


class NoContentReadyError(FirstPostError):
    """Nenhum conteudo pronto para publicacao."""


class PackageError(FirstPostError):
    """Erro ao empacotar conteudo para publicacao."""
