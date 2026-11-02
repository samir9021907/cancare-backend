"""
Application Entrypoint for CaneCare AI.
Re-exports the FastAPI app instance for Uvicorn and deployment platforms.
"""

from app.main import app

__all__ = ["app"]
