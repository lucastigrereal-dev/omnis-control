"""Memory Pack module errors."""


class MemoryPackError(Exception):
    """Erro base do modulo Memory Pack."""
    pass


class QueryValidationError(MemoryPackError):
    """Query de memoria invalida."""
    pass


class EmptyQueryError(QueryValidationError):
    """Query de memoria esta vazia."""
    pass


class InvalidSourceError(QueryValidationError):
    """Fonte de memoria invalida."""
    pass


class InvalidSectorError(QueryValidationError):
    """Setor invalido."""
    pass


class ContextPackError(MemoryPackError):
    """Erro ao montar context pack."""
    pass


class EmptyHitListError(ContextPackError):
    """Lista de hits vazia ao montar context pack."""
    pass


class RankingError(MemoryPackError):
    """Erro ao ranquear memory hits."""
    pass


class WritePlanError(MemoryPackError):
    """Erro ao criar plano de writeback."""
    pass


class DestructiveActionBlockedError(WritePlanError):
    """Acao destrutiva bloqueada por regra de seguranca."""
    pass


class WritebackBlockedError(WritePlanError):
    """Writeback bloqueado — modulo opera em modo dry-run."""
    pass


class AkashaConnectionProhibitedError(MemoryPackError):
    """Conexao real com Akasha proibida neste modulo."""
    pass


class ExportError(MemoryPackError):
    """Erro ao exportar context pack."""
    pass


class InvalidFormatError(ExportError):
    """Formato de exportacao invalido."""
    pass


class SerializationError(MemoryPackError):
    """Erro ao serializar/desserializar modelos."""
    pass
