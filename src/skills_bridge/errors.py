class SkillBridgeError(Exception):
    pass


class SkillNotFoundError(SkillBridgeError):
    pass


class DryRunError(SkillBridgeError):
    pass
