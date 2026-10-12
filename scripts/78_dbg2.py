# -*- coding: utf-8 -*-
"""Why still g0534? terms from 'レイアウトとは？' -> after strip: 'レイアウト'
(len5). head g0533='レイアウト'(5) should score 3.0; g0534='レイアウト撮'(6)
> 5+1=6? len(head)<=len(t)+1 -> 6<=6 True -> also 3.0. Tie -> first wins (g0534
is block 0 = top hit). Need strict: len(head) <= len(t)."""
import re
import sys
sys.path.insert(0, ".")
from app.generation.demo_client import ExtractiveDemoClient as D

print("terms now:", D._terms("レイアウトとは？"))
