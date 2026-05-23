from src.content_queue.accounts import Account, AccountRegistry


def test_account_round_trip_preserves_optional_fields():
    account = Account(
        account_id="acct-1",
        handle="lucastigrereal",
        display_name="Lucas Tigre",
        instagram_user_id="ig-1",
        notes="pilot",
    )

    restored = Account.from_dict(account.to_dict())

    assert restored == account


def test_account_registry_add_update_and_deactivate(tmp_path):
    registry = AccountRegistry(str(tmp_path / "accounts.jsonl"))

    created = registry.add("@LucasTigreReal", tags="familia,viagem")
    updated = registry.update(created.handle, priority="high")
    deactivated = registry.deactivate(created.handle)

    assert created.handle == "lucastigrereal"
    assert created.tags == ["familia", "viagem"]
    assert updated is not None
    assert updated.priority == "high"
    assert deactivated is not None
    assert deactivated.active is False
