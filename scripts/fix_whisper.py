# -*- coding: utf-8 -*-
"""Transcribe with openai-whisper (ffmpeg CLI decode, no av binding)."""
import subprocess, sys

r = subprocess.run(["uv", "pip", "install", "--python", ".venv/bin/python",
                    "openai-whisper", "numba==0.61.2", "llvmlite==0.44.1"],
                   capture_output=True, text=True)
print(r.stdout[-500:], r.stderr[-300:])
r2 = subprocess.run([".venv/bin/python", "-c", "import whisper; print('whisper ok')"],
                    capture_output=True, text=True)
print(r2.stdout, r2.stderr[-300:])
