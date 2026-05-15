from src.observability.models import AuditEntry, AuditEntryType, _now_iso


class AuditTrail:
    def __init__(self):
        self._entries: list[AuditEntry] = []

    def record(
        self,
        action: str,
        result: str,
        source: str = "",
        entry_type: AuditEntryType = AuditEntryType.EXECUTION,
        detail: dict | None = None,
    ) -> AuditEntry:
        entry = AuditEntry(
            action=action,
            result=result,
            source=source,
            entry_type=entry_type,
            detail=detail or {},
        )
        self._entries.append(entry)
        return entry

    def query(
        self,
        source: str = "",
        entry_type: str = "",
    ) -> list[AuditEntry]:
        results = self._entries
        if source:
            results = [e for e in results if e.source == source]
        if entry_type:
            results = [e for e in results if e.entry_type.value == entry_type]
        return results

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    @property
    def last_entry(self) -> AuditEntry | None:
        return self._entries[-1] if self._entries else None
