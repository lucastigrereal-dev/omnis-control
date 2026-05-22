class SkillRouterError(Exception):
    """Base error for skill router bridge operations."""
    pass


class SkillNotAvailableError(SkillRouterError):
    def __init__(self, skill_id: str):
        super().__init__(f"Skill not available: {skill_id}")


class CatalogLoadError(SkillRouterError):
    def __init__(self, path: str, reason: str):
        super().__init__(f"Failed to load catalog from {path}: {reason}")


class DispatchError(SkillRouterError):
    def __init__(self, skill_id: str, reason: str):
        super().__init__(f"Dispatch failed for {skill_id}: {reason}")
