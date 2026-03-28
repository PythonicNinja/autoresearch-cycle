"""Local-first autoresearch reference implementation."""

from .api import create_app
from .services import build_service

__all__ = ["build_service", "create_app"]
