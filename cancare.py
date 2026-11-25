import os
import sys

# Root runner that delegates to canecare-backend
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "canecare-backend")
os.chdir(backend_dir)

runner = os.path.join(backend_dir, "cancare.py")
with open(runner, "r", encoding="utf-8") as f:
    code = f.read()

exec(compile(code, runner, "exec"), {"__name__": "__main__", "__file__": runner})

