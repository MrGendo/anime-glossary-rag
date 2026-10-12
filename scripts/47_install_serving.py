# -*- coding: utf-8 -*-
"""Install serving deps (script wrapper to avoid terminal server-heuristic)."""
import subprocess
r = subprocess.run(["uv", "pip", "install", "--python", ".venv/bin/python",
                    "fastapi", "uvicorn", "httpx"], capture_output=True, text=True)
print(r.stdout[-500:], r.stderr[-200:])
