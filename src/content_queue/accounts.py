"""Account Registry — Cadastro local de contas Instagram.

Fonte canônica operacional do OMNIS.
CLAUDE.md permanece como documentação/contexto humano.
"""

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ACCOUNTS_PATH = os.path.expanduser("~/omnis-control/data/accounts.jsonl")
DEFAULT_POSTING_TIMES = ["08:50", "17:50", "20:50"]
DEFAULT_FORMATS = ["reels", "stories", "feed", "carousel"]


class Priority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def _normalize_handle(handle: str) -> str:
    return handle.strip().lstrip("@").lower()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Account:
    account_id: str
    handle: str
    platform: str = "instagram"
    display_name: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    default_posting_times: list[str] = field(default_factory=lambda: list(DEFAULT_POSTING_TIMES))
    default_formats: list[str] = field(default_factory=lambda: list(DEFAULT_FORMATS))
    priority: str = Priority.MEDIUM
    active: bool = True
    instagram_user_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Account":
        return cls(**data)


class AccountRegistry:
    """Gerencia o arquivo JSONL de contas."""

    def __init__(self, path: str = ACCOUNTS_PATH):
        self.path = path
        Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)

    def add(self, handle: str, **kwargs) -> Account:
        """Adiciona nova conta. Erro se handle já existir."""
        handle_norm = _normalize_handle(handle)
        existing = self.get_by_handle(handle_norm)
        if existing:
            raise ValueError(f"Account '{handle_norm}' já existe (id: {existing.account_id})")

        account = Account(
            account_id=kwargs.pop("account_id", uuid.uuid4().hex[:12]),
            handle=handle_norm,
            **kwargs,
        )
        if "tags" in kwargs and isinstance(kwargs["tags"], str):
            account.tags = [t.strip() for t in kwargs["tags"].split(",") if t.strip()]
        account.created_at = _now_iso()
        account.updated_at = account.created_at
        self._append(account)
        return account

    def get_by_handle(self, handle: str) -> Optional[Account]:
        """Busca conta por handle normalizado."""
        handle_norm = _normalize_handle(handle)
        for a in self.list_all():
            if a.handle == handle_norm:
                return a
        return None

    def get(self, account_id: str) -> Optional[Account]:
        for a in self.list_all():
            if a.account_id == account_id:
                return a
        return None

    def update(self, handle: str, **kwargs) -> Optional[Account]:
        """Atualiza campos de uma conta."""
        handle_norm = _normalize_handle(handle)
        accounts = self.list_all()
        found = None
        for i, a in enumerate(accounts):
            if a.handle == handle_norm:
                for key, val in kwargs.items():
                    if hasattr(a, key) and val is not None:
                        if key == "tags" and isinstance(val, str):
                            val = [t.strip() for t in val.split(",") if t.strip()]
                        setattr(a, key, val)
                a.updated_at = _now_iso()
                found = a
                accounts[i] = a
                break
        if found:
            self._rewrite(accounts)
        return found

    def deactivate(self, handle: str) -> Optional[Account]:
        """Desativa uma conta."""
        return self.update(handle, active=False)

    def list_all(self) -> list[Account]:
        if not os.path.isfile(self.path):
            return []
        accounts = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        accounts.append(Account.from_dict(json.loads(line)))
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        return accounts

    def list_active(self) -> list[Account]:
        return [a for a in self.list_all() if a.active]

    def count(self) -> int:
        if not os.path.isfile(self.path):
            return 0
        with open(self.path, encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())

    def _append(self, account: Account):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(account.to_dict(), ensure_ascii=False) + "\n")

    def _rewrite(self, accounts: list[Account]):
        with open(self.path, "w", encoding="utf-8") as f:
            for a in accounts:
                f.write(json.dumps(a.to_dict(), ensure_ascii=False) + "\n")
