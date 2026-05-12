"""P13 Analytics/BI Skeleton — deterministic analytics & BI package.

Scope:
- Metric definition and event recording (dry-run)
- Dashboard specification planning
- Report specification planning
- Dataset validation
- Local JSON + Markdown exporters

Constraints: zero LLM, zero network, zero Docker, zero database.
"""

from src.analytics.errors import (
    AnalyticsError,
    DashboardError,
    DatasetEmptyError,
    DatasetSchemaMismatchError,
    ExportError,
    InvalidDatasetError,
    InvalidMetricError,
    ReportError,
)
from src.analytics.exporters import export_dashboard_json, export_report_markdown
from src.analytics.models import (
    VALID_AGGREGATIONS,
    VALID_CATEGORIES,
    VALID_LAYOUTS,
    VALID_REPORT_FORMATS,
    VALID_UNITS,
    VALID_WIDGET_TYPES,
    AnalyticsDataset,
    DashboardSpec,
    MetricDefinition,
    MetricEvent,
    ReportSpec,
)
from src.analytics.service import (
    AnalyticsPlanner,
    MetricSummary,
    ValidationResult,
)

__all__ = [
    # Models
    "MetricDefinition",
    "MetricEvent",
    "AnalyticsDataset",
    "DashboardSpec",
    "ReportSpec",
    # Constants
    "VALID_AGGREGATIONS",
    "VALID_CATEGORIES",
    "VALID_LAYOUTS",
    "VALID_REPORT_FORMATS",
    "VALID_UNITS",
    "VALID_WIDGET_TYPES",
    # Service
    "AnalyticsPlanner",
    "MetricSummary",
    "ValidationResult",
    # Errors
    "AnalyticsError",
    "InvalidMetricError",
    "InvalidDatasetError",
    "DatasetEmptyError",
    "DatasetSchemaMismatchError",
    "DashboardError",
    "ReportError",
    "ExportError",
    # Exporters
    "export_dashboard_json",
    "export_report_markdown",
]
