"""W18-B1/W20 — Auth API Key para OMNIS FastAPI.

Modo dev: se OMNIS_API_KEY não estiver no ambiente, todas as requisições
são permitidas (sem auth). Útil para testes locais e KRATOS dev.

Modo prod: OMNIS_API_KEY obrigatório no header X-KRATOS-KEY (canônico) ou
Authorization: Bearer <key>.

Uso:
    from src.api.auth import require_api_key, dev_mode

    @router.get("/endpoint", dependencies=[Depends(require_api_key)])
    def endpoint(): ...
"""
from __future__ import annotations

import os
from functools import lru_cache

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

_KRATOS_KEY_HEADER = APIKeyHeader(name="X-KRATOS-KEY", auto_error=False)
_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
_BEARER_HEADER = APIKeyHeader(name="Authorization", auto_error=False)


@lru_cache(maxsize=1)
def _configured_key() -> str | None:
    """Retorna a API key configurada ou None (dev mode)."""
    return os.environ.get("OMNIS_API_KEY") or None


def dev_mode() -> bool:
    """True se nenhuma API key estiver configurada (modo dev)."""
    return _configured_key() is None


def require_api_key(
    x_kratos_key: str | None = Security(_KRATOS_KEY_HEADER),
    x_api_key: str | None = Security(_API_KEY_HEADER),
    authorization: str | None = Security(_BEARER_HEADER),
) -> bool:
    """FastAPI dependency — verifica API key.

    - Dev mode (OMNIS_API_KEY não set): sempre passa.
    - Prod mode: exige X-KRATOS-KEY (canônico) ou aliases temporários.
    """
    key = _configured_key()
    if key is None:
        # Dev mode — sem autenticação
        return True

    # Header canônico v1
    if x_kratos_key and x_kratos_key == key:
        return True

    # Alias temporário para migração
    # Extrai a chave do header X-API-Key
    if x_api_key and x_api_key == key:
        return True

    # Extrai a chave do header Authorization: Bearer <key>
    if authorization:
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1] == key:
            return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "API key inválida ou ausente. Use X-KRATOS-KEY "
            "(ou aliases temporários X-API-Key/Bearer)."
        ),
    )
