"""OMNIS Legos — implementações dos contratos de interface externos."""
from .browser_executor_lego import BrowserExecutorLego
from .code_executor_lego import CodeExecutorLego
from .video_processor_lego import VideoProcessorLego
from .research_conductor_lego import ResearchConductorLego
from .channel_messenger_lego import ChannelMessengerLego
from .registry import LegoRegistry, default_registry

__all__ = [
    "BrowserExecutorLego",
    "CodeExecutorLego",
    "VideoProcessorLego",
    "ResearchConductorLego",
    "ChannelMessengerLego",
    "LegoRegistry",
    "default_registry",
]
