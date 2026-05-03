"""Video Asset Registry — Rastreamento local de assets de vídeo."""

from .models import VideoAsset, AssetStatus, AssetSourceType, AssetFormat
from .registry import Registry
from .scanner import Scanner
from .queue import Queue

__all__ = ["VideoAsset", "AssetStatus", "AssetSourceType", "AssetFormat", "Registry", "Scanner", "Queue"]
