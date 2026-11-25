import os
import sys

# Ensure canecare-backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Ensure venv site-packages is in sys.path so it works with global python as well
venv_site = os.path.join(backend_dir, "venv", "Lib", "site-packages")
if os.path.exists(venv_site) and venv_site not in sys.path:
    sys.path.insert(0, venv_site)

try:
    import uvicorn
except ImportError as e:
    print("Error: Could not load dependencies:", e)
    print("Please activate the virtual environment:")
    print("  .\\venv\\Scripts\\activate")
    sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("🌾 CaneCare AI Backend Server Starting...")
    print("👉 API Documentation (Swagger): http://127.0.0.1:8000/docs")
    print("👉 Health Check:                http://127.0.0.1:8000/api/v1/health")
    print("=" * 60)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

