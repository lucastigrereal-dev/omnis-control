"""P28 Self-Improvement Loop — continuous learning and improvement."""
from src.self_improvement.models import (
    ExecutionFeedback, ImprovementProposal, ImpactMeasurement,
    Pattern, PrioritizedGap,
    SOURCE_MISSION, SOURCE_BUILD, SOURCE_ACTION, SOURCE_SYSTEM,
    CATEGORY_CAPABILITY_GAP, CATEGORY_PERFORMANCE, CATEGORY_RELIABILITY,
    CATEGORY_COST, CATEGORY_SECURITY,
    PROPOSAL_DRAFT, PROPOSAL_PROPOSED, PROPOSAL_APPROVED, PROPOSAL_REJECTED,
    PROPOSAL_IMPLEMENTED, PROPOSAL_MEASURED,
    VERDICT_IMPROVED, VERDICT_DEGRADED, VERDICT_NEUTRAL, VERDICT_INSUFFICIENT_DATA,
)
from src.self_improvement.errors import (
    ImprovementError, AnalysisError, ProposalError, ExecutionError,
    MeasurementError, InsufficientDataError, RollbackError,
)
from src.self_improvement.collector import FeedbackCollector
from src.self_improvement.analyzer import PatternAnalyzer
from src.self_improvement.prioritizer import GapPrioritizer
from src.self_improvement.proposer import ImprovementProposer
from src.self_improvement.executor import ImprovementExecutor
from src.self_improvement.measurer import ImpactMeasurer

__all__ = [
    # Models
    "ExecutionFeedback", "ImprovementProposal", "ImpactMeasurement",
    "Pattern", "PrioritizedGap",
    # Constants
    "SOURCE_MISSION", "SOURCE_BUILD", "SOURCE_ACTION", "SOURCE_SYSTEM",
    "CATEGORY_CAPABILITY_GAP", "CATEGORY_PERFORMANCE", "CATEGORY_RELIABILITY",
    "CATEGORY_COST", "CATEGORY_SECURITY",
    "PROPOSAL_DRAFT", "PROPOSAL_PROPOSED", "PROPOSAL_APPROVED", "PROPOSAL_REJECTED",
    "PROPOSAL_IMPLEMENTED", "PROPOSAL_MEASURED",
    "VERDICT_IMPROVED", "VERDICT_DEGRADED", "VERDICT_NEUTRAL", "VERDICT_INSUFFICIENT_DATA",
    # Core
    "FeedbackCollector", "PatternAnalyzer", "GapPrioritizer",
    "ImprovementProposer", "ImprovementExecutor", "ImpactMeasurer",
    # Errors
    "ImprovementError", "AnalysisError", "ProposalError", "ExecutionError",
    "MeasurementError", "InsufficientDataError", "RollbackError",
]
