"""Asset Inbox errors."""


class AssetInboxScanError(ValueError):
    """Raised when the scan root path is invalid or inaccessible."""


class PathTraversalError(ValueError):
    """Raised when a path traversal attempt is detected."""


class FingerprintError(IOError):
    """Raised when fingerprint computation fails for a specific file."""
