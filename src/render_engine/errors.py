"""Render engine errors."""


class RenderEngineError(Exception):
    pass


class PackageNotFoundError(RenderEngineError):
    pass


class RenderFailedError(RenderEngineError):
    pass
