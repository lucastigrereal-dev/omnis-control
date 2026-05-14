class WorkOrderError(Exception):
    pass


class ParseError(WorkOrderError):
    pass


class MapError(WorkOrderError):
    pass


class InvalidWorkOrderError(WorkOrderError):
    pass
