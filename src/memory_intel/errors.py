"""P21 Memory Intelligence errors."""


class MemoryIntelError(Exception):
    """Base error for P21 Memory Intelligence."""


class RetrievalError(MemoryIntelError):
    """Falha na recuperacao de contexto."""


class WritebackError(MemoryIntelError):
    """Falha na persistencia de aprendizados."""


class ContextTooLargeError(MemoryIntelError):
    """assembled_text excede o limite maximo de caracteres."""


class NoSourcesAvailableError(MemoryIntelError):
    """Nenhuma fonte disponivel para o intent solicitado."""


class SimilarityError(MemoryIntelError):
    """Falha no calculo de similaridade entre missoes."""


class SafetyViolationError(MemoryIntelError):
    """Violacao de regra de seguranca da memoria."""
