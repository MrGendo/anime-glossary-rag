# -*- coding: utf-8 -*-
"""Fix av version in venv for faster-whisper compat."""
import subprocess
r = subprocess.run(["uv", "pip", "install", "--python", ".venv/bin/python", "av==14.4.0"],
                   capture_output=True, text=True)
print(r.stdout[-800:])
print(r.stderr[-400:])
r2 = subprocess.run([".venv/bin/python", "-c", "import av; print('av', av.__version__)"],
                    capture_output=True, text=True)
print(r2.stdout, r2.stderr[-200:])
