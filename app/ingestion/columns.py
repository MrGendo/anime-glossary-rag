# -*- coding: utf-8 -*-
"""Column reconstruction from Vision OCR boxes (normalized coords, y from bottom).

Mirrors scripts/11 logic so app code can reuse it; scripts remain the
executable pipeline of record."""
from __future__ import annotations

from typing import List


def _merge_same_line(col: List[dict]) -> List[dict]:
    lines, cur = [], None
    for b in sorted(col, key=lambda b: (-b["y"], b["x"])):
        if cur and abs(cur["y"] - b["y"]) < min(cur["h"], b["h"]) * 0.5:
            cur["text"] += b["text"]
        else:
            if cur:
                lines.append(cur)
            cur = dict(b)
    if cur:
        lines.append(cur)
    return lines


def reconstruct_columns(boxes: List[dict], ncols: int = 2,
                        drop_header_above_y: float = 0.93) -> List[List[dict]]:
    """Split boxes into ncols columns by x-center; per column merge same-line
    boxes and return reading order (top->bottom). Running headers (y > 0.93)
    are dropped."""
    cols: List[List[dict]] = [[] for _ in range(ncols)]
    for b in boxes:
        if b.get("y", 0) > drop_header_above_y:
            continue
        cx = b["x"] + b["w"] / 2
        ci = min(int(cx * ncols), ncols - 1)
        cols[ci].append(b)
    return [_merge_same_line(c) for c in cols]
