class SkillBridgeError(Exception):
    pass


class SkillNotFoundError(SkillBridgeError):
    pass


class DryRunError(SkillBridgeError):
    pass


class CatalogLoadError(SkillBridgeError):
    """Failed to load skill catalog from path."""

    def __init__(self, path: str, detail: str = ""):
        self.path = path
        self.detail = detail
        super().__init__(f"Failed to load catalog from {path}: {detail}")


class DispatchError(SkillBridgeError):
    """Real dispatch attempted but not implemented."""

    def __init__(self, skill_id: str, reason: str = ""):
        self.skill_id = skill_id
        super().__init__(f"Dispatch error for {skill_id}: {reason}")


class SkillNotAvailableError(SkillBridgeError):
    """Skill not available in catalog."""
