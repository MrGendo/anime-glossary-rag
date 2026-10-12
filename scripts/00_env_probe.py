# -*- coding: utf-8 -*-
"""Probe available OCR toolchains on this machine (no changes, read-only checks)."""
import importlib, shutil, subprocess, sys

print("== binaries ==")
for b in ["tesseract", "brew", "paddleocr", "docker", "cloudflared", "tunnel", "gh"]:
    p = shutil.which(b)
    print(f"{b}: {p}")

print("\n== python 3.14 site-packages (via uv venv to be created later; check user site) ==")
for py in ["python3.14", "python3.11", "python3"]:
    try:
        out = subprocess.run([py, "-m", "pip", "list"], capture_output=True, text=True, timeout=60)
        rel = [l for l in out.stdout.splitlines() if any(k in l.lower() for k in
               ["mupdf", "fitz", "tesseract", "paddle", "vision", "faiss", "sentence", "bm25", "fastapi", "pydantic", "numpy", "httpx", "pillow"])]
        print(f"--- {py} ---")
        print("\n".join(rel) if rel else "(none of the relevant pkgs)")
    except Exception as e:
        print(f"--- {py} err: {e}")

print("\n== macOS Vision via pyobjc ==")
try:
    import Vision  # noqa
    print("pyobjc Vision available in current interpreter")
except Exception as e:
    print("Vision import failed:", e)

print("\n== swift OCR helper from memory ==")
for p in ["/tmp/swift_ocr.swift", "/tmp/ocr.swift"]:
    print(p, "exists:", __import__("os").path.exists(p))
