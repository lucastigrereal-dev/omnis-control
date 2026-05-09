"""Quality layer errors."""


class QualityLayerError(Exception):
    pass


class PackageNotFoundError(QualityLayerError):
    pass
