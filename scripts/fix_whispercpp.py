# -*- coding: utf-8 -*-
"""Transcribe via whisper.cpp CLI (no python deps) — install binary via brew."""
import subprocess
r = subprocess.run(["brew", "install", "whisper-cpp"],
                   capture_output=True, text=True, timeout=1200)
print(r.stdout[-600:])
print("ERR:", r.stderr[-400:])
