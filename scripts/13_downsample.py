# -*- coding: utf-8 -*-
"""Downsample 3 pages for vision check."""
from PIL import Image
for p in [101, 115, 164]:
    im = Image.open(f"data/raw/pages_all/p{p:03d}.png")
    im = im.resize((im.width // 2, im.height // 2))
    im.save(f"data/raw/pages_all/p{p:03d}_half.png")
    print(p, im.size)
