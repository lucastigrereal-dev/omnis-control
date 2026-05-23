"""OMNIS Lego Interfaces — contratos para executores externos."""
from .browser_executor import BrowserExecutor, BrowserTask, BrowserResult
from .code_executor import CodeExecutor, CodeSpec, CodeResult
from .video_processor import VideoProcessor, VideoSpec, VideoResult
from .research_conductor import (
    ResearchConductor, ResearchSpec, ResearchResult,
    ResearchPerspective, ResearchCitation,
)

__all__ = [
    "BrowserExecutor", "BrowserTask", "BrowserResult",
    "CodeExecutor", "CodeSpec", "CodeResult",
    "VideoProcessor", "VideoSpec", "VideoResult",
    "ResearchConductor", "ResearchSpec", "ResearchResult",
    "ResearchPerspective", "ResearchCitation",
]
