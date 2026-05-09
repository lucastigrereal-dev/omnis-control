"""Offline Delivery Factory — exceptions."""


class OfflineFactoryError(Exception):
    """Base error for offline factory."""


class PackageCreationError(OfflineFactoryError):
    """Failed to create a delivery package."""


class ManifestError(OfflineFactoryError):
    """Manifest generation error."""


class ExportError(OfflineFactoryError):
    """File export error."""


class MissingDependencyError(OfflineFactoryError):
    """Required data missing (caption, queue item, etc.)."""
