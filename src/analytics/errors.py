"""P13 Analytics/BI — error hierarchy."""


class AnalyticsError(Exception):
    """Base error for the analytics package."""
    pass


class InvalidMetricError(AnalyticsError):
    """Metric definition fails validation."""
    pass


class InvalidDatasetError(AnalyticsError):
    """Dataset structure or integrity issue."""
    pass


class DatasetEmptyError(InvalidDatasetError):
    """Dataset has no events."""
    pass


class DatasetSchemaMismatchError(InvalidDatasetError):
    """Dataset events don't match registered metric definitions."""
    pass


class DashboardError(AnalyticsError):
    """Dashboard spec is invalid."""
    pass


class ReportError(AnalyticsError):
    """Report spec is invalid."""
    pass


class ExportError(AnalyticsError):
    """Export operation failed."""
    pass
