"""Excecoes do modulo Video Studio."""


class VideoStudioError(Exception):
    """Erro base do modulo Video Studio."""
    pass


class InvalidVideoSourceError(VideoStudioError):
    """Fonte de video invalida."""
    pass


class InvalidTranscriptError(VideoStudioError):
    """Segmento de transcricao invalido."""
    pass


class InvalidCutPlanError(VideoStudioError):
    """Plano de corte invalido."""
    pass


class InvalidReelScriptError(VideoStudioError):
    """Roteiro de reel invalido."""
    pass


class InvalidVideoPackageError(VideoStudioError):
    """Pacote de video invalido."""
    pass


class ValidationError(VideoStudioError):
    """Falha na validacao do pacote de video."""
    pass
