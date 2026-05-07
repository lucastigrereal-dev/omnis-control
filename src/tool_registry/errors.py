"""Tool Registry errors — P0.8."""
from __future__ import annotations


class ToolRegistryError(Exception):
    """Erro base do Tool Registry."""


class ToolNotFoundError(ToolRegistryError):
    """Tool ID nao encontrado."""


class DuplicateToolError(ToolRegistryError):
    """Tool ID ja registrado."""


class InvalidToolIdError(ToolRegistryError):
    """Tool ID nao passa validacao de slug."""


class InvalidStatusError(ToolRegistryError):
    """Status invalido para ferramenta."""


class InvalidCategoryError(ToolRegistryError):
    """Categoria invalida."""


class SecretDetectedError(ToolRegistryError):
    """Credential parece conter valor real de secret — bloqueado."""


class ValidationError(ToolRegistryError):
    """Erro de validacao generico."""
