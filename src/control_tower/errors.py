class ControlTowerError(Exception):
    pass


class RiskBlockedError(ControlTowerError):
    pass


class BoundaryViolationError(ControlTowerError):
    pass
