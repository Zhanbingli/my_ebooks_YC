"""Shared tooling for building eBooks from YouTube transcripts."""

from pathlib import Path

__all__ = ["__version__", "PROJECT_ROOT"]

__version__ = "0.1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
