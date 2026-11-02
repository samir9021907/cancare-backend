"""
Root application entrypoint for cloud hosting (Render, Railway, Heroku).
Loads and re-exports the CaneCare AI FastAPI application from canecare-backend.
"""

import sys
import os
import importlib

# Add backend directory to sys.path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "canecare-backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Dynamically import the app module cleanly to avoid static linter missing-import warnings
app_main_module = importlib.import_module("app.main")
app = getattr(app_main_module, "app")

__all__ = ["app"]
