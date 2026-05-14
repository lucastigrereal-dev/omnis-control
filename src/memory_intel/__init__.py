"""P21 Memory Intelligence — contextual retrieval and learning writeback engine."""
from src.memory_intel.models import (
    MemoryIntelConfig,
    MissionSimilarityResult,
    RetrievalResult,
    PatternResult,
    MemoryIntelMode,
    INTENT_CREATE_CAMPAIGN,
    INTENT_PUBLISH_CONTENT,
    INTENT_DELIVER_TO_CLIENT,
    INTENT_ANALYZE_PERFORMANCE,
    INTENT_COMMERCIAL_OUTREACH,
    VALID_INTENTS,
    INTENT_TO_SOURCES,
    SIMILARITY_WEIGHT_INTENT,
    SIMILARITY_WEIGHT_SECTOR,
    SIMILARITY_WEIGHT_TAGS,
    SIMILARITY_WEIGHT_MODULES,
    MAX_ASSEMBLED_TEXT_CHARS,
    MAX_SNIPPET_CHARS,
    MAX_HITS_PER_SOURCE,
    MAX_RECORDS_PER_MISSION,
    MAX_SIMILAR_MISSIONS_RESULTS,
    DEFAULT_MAX_HITS,
    MIN_SIMILARITY_THRESHOLD,
)
from src.memory_intel.service import MemoryIntelligence
from src.memory_intel.similarity import find_similar_missions, compute_similarity_score
from src.memory_intel.safety import sanitize_context_text, validate_safety_rules
from src.memory_intel.errors import (
    MemoryIntelError,
    RetrievalError,
    WritebackError,
    ContextTooLargeError,
    NoSourcesAvailableError,
    SimilarityError,
    SafetyViolationError,
)

__all__ = [
    # Models
    "MemoryIntelConfig",
    "MissionSimilarityResult",
    "RetrievalResult",
    "PatternResult",
    "MemoryIntelMode",
    # Intent constants
    "INTENT_CREATE_CAMPAIGN",
    "INTENT_PUBLISH_CONTENT",
    "INTENT_DELIVER_TO_CLIENT",
    "INTENT_ANALYZE_PERFORMANCE",
    "INTENT_COMMERCIAL_OUTREACH",
    "VALID_INTENTS",
    "INTENT_TO_SOURCES",
    # Similarity weights
    "SIMILARITY_WEIGHT_INTENT",
    "SIMILARITY_WEIGHT_SECTOR",
    "SIMILARITY_WEIGHT_TAGS",
    "SIMILARITY_WEIGHT_MODULES",
    # Limits
    "MAX_ASSEMBLED_TEXT_CHARS",
    "MAX_SNIPPET_CHARS",
    "MAX_HITS_PER_SOURCE",
    "MAX_RECORDS_PER_MISSION",
    "MAX_SIMILAR_MISSIONS_RESULTS",
    "DEFAULT_MAX_HITS",
    "MIN_SIMILARITY_THRESHOLD",
    # Service
    "MemoryIntelligence",
    # Similarity
    "find_similar_missions",
    "compute_similarity_score",
    # Safety
    "sanitize_context_text",
    "validate_safety_rules",
    # Errors
    "MemoryIntelError",
    "RetrievalError",
    "WritebackError",
    "ContextTooLargeError",
    "NoSourcesAvailableError",
    "SimilarityError",
    "SafetyViolationError",
]
