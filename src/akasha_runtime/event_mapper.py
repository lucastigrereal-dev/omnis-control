from src.akasha_runtime.models import AkashaEventMapping


class AkashaEventMapper:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._mappings: dict[str, AkashaEventMapping] = {}
        self._mapped_count: int = 0

    def register(self, mapping: AkashaEventMapping) -> None:
        self._mappings[mapping.event_type] = mapping

    def register_batch(self, mappings: list[AkashaEventMapping]) -> None:
        for m in mappings:
            self.register(m)

    def map_event(self, event_type: str) -> tuple[str | None, AkashaEventMapping | None]:
        mapping = self._mappings.get(event_type)
        if mapping is None:
            return None, None
        self._mapped_count += 1
        return mapping.target_collection, mapping

    def map_batch(self, events: list[dict]) -> list[dict]:
        results = []
        for event in events:
            event_type = event.get("event_type", "")
            collection, mapping = self.map_event(event_type)
            results.append({
                "event_type": event_type,
                "target_collection": collection,
                "mapped": collection is not None,
                "require_approval": mapping.require_approval if mapping else False,
                "transform_hint": mapping.transform_hint if mapping else "",
            })
        return results

    def get_mapping(self, event_type: str) -> AkashaEventMapping | None:
        return self._mappings.get(event_type)

    def unregister(self, event_type: str) -> bool:
        if event_type in self._mappings:
            del self._mappings[event_type]
            return True
        return False

    @property
    def mapped_count(self) -> int:
        return self._mapped_count

    @property
    def mapping_count(self) -> int:
        return len(self._mappings)
