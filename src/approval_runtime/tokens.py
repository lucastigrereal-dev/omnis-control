import uuid
import secrets
from datetime import datetime, timezone
from typing import Optional

from src.approval_runtime.errors import InvalidTokenError


class TokenVerifier:
    def __init__(self, tokens: Optional[dict[str, str]] = None):
        self._tokens: dict[str, str] = {}
        self._used_tokens: set[str] = set()
        if tokens:
            self._tokens.update(tokens)

    def generate_token(self, request_id: str) -> str:
        token = f"omnis_approval_{uuid.uuid4().hex}"
        self._tokens[request_id] = token
        return token

    def verify(self, request_id: str, token: str) -> bool:
        if request_id not in self._tokens:
            raise InvalidTokenError(token)
        if token != self._tokens[request_id]:
            raise InvalidTokenError(token)
        if token in self._used_tokens:
            raise InvalidTokenError(token)
        self._used_tokens.add(token)
        return True

    def revoke(self, request_id: str) -> None:
        self._tokens.pop(request_id, None)
