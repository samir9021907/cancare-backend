"""
Root entry point for cloud deployment platforms (Render, Railway, Heroku).
Redirects execution into the canecare-backend application.
"""

import sys
import os

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "canecare-backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import the FastAPI application
from app.main import app

__all__ = ["app"]
