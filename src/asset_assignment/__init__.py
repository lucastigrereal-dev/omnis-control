"""Asset Assignment Center — P1.9.

Connects VideoAsset registry + ContentQueue + CaptionApproval
to produce packages with READY status.
"""
from .models import AssetAssignmentResult
from .service import check_assignment_status, add_mock_asset, list_ready_candidates

__all__ = [
    "AssetAssignmentResult",
    "check_assignment_status",
    "add_mock_asset",
    "list_ready_candidates",
]