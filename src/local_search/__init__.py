"""Local Search Engine — unified search across missions, templates, skills, and logs."""

from .models import SearchResult, SearchQuery, SourceType
from .engine import SearchEngine

__all__ = ["SearchResult", "SearchQuery", "SourceType", "SearchEngine"]
