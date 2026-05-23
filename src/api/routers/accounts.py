"""GET /accounts — cadastro de contas Instagram."""
from fastapi import APIRouter, HTTPException
from src.content_queue import AccountRegistry

router = APIRouter()


@router.get("")
def list_accounts() -> dict:
    reg = AccountRegistry()
    accounts = reg.list_all()
    return {"total": len(accounts), "accounts": [a.to_dict() for a in accounts]}


@router.get("/active")
def list_active_accounts() -> dict:
    reg = AccountRegistry()
    accounts = reg.list_active()
    return {"total": len(accounts), "accounts": [a.to_dict() for a in accounts]}


@router.get("/{account_id}")
def get_account(account_id: str) -> dict:
    reg = AccountRegistry()
    account = reg.get(account_id)
    if not account:
        raise HTTPException(404, f"Conta não encontrada: {account_id}")
    return account.to_dict()
