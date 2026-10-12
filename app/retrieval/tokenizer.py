"""Tokenizer shared by the lexical retrievers.

Rules (per task spec):
- Japanese text (hiragana / katakana / CJK ideographs) -> character bigrams.
- Latin / digits -> lowercase whole words.
- Anything else (spaces, punctuation) acts as a separator.

Hiragana/katakana covering also folds prolonged-sound marks and the two
kana iterations marks into the kana ranges so bigrams chain across them.
"""

from __future__ import annotations

import re
from typing import List

# Latin word: ASCII letters/digits/underscore sequences (underscore rare in JA text).
_LATIN_RE = re.compile(r"[0-9A-Za-z]+(?:['][0-9A-Za-z]+)*")
# Full-width alphanumerics are treated as Latin too (normalized to lower).
_FW_RE = re.compile(r"[０-９Ａ-Ｚａ-ｚ]+")

_HIRAGANA = "ぁ-ゖ"
_KATAKANA = "ァ-ヿ"
_PROLONGED = "ー"
_ITERATION = "々〆ヾヽ"  # repeat/composite marks common in glossary terms
_CJK = "一-鿿"  # U+4E00..U+9FFF
_CJK_EXT = "㐀-䶿"

_JA_RE = re.compile(
    f"[{_HIRAGANA}{_KATAKANA}{_PROLONGED}{_ITERATION}{_CJK}{_CJK_EXT}]"
)


def _normalize(text: str) -> str:
    """NFKC-style normalization for the cases we care about (no extra deps)."""
    import unicodedata

    return unicodedata.normalize("NFKC", text)


def tokenize(text: str, use_bigram: bool = True) -> List[str]:
    """Tokenize mixed Japanese/Latin text.

    - Latin runs become single lowercase tokens ("Action" -> "action").
    - Japanese runs become character bigrams ("作画" -> ["作画"],
      "作画監督" -> ["作画", "画作", "監画"? ...]) -- precisely: every adjacent
      pair inside the run; a single-character run yields that character.
    - ``use_bigram=False`` returns unigrams for Japanese instead (used by
      exact-match helpers).
    """
    if not text:
        return []
    text = _normalize(text)
    tokens: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if _JA_RE.match(ch):
            j = i
            while j < n and _JA_RE.match(text[j]):
                j += 1
            run = text[i:j]
            if use_bigram:
                if len(run) == 1:
                    tokens.append(run)
                else:
                    tokens.extend(run[k : k + 2] for k in range(len(run) - 1))
            else:
                tokens.extend(run)
            i = j
        elif _LATIN_RE.match(ch):
            m = _LATIN_RE.match(text, i)
            assert m is not None
            tokens.append(m.group(0).lower())
            i = m.end()
        elif _FW_RE.match(ch):
            m = _FW_RE.match(text, i)
            assert m is not None
            tokens.append(_normalize(m.group(0)).lower())
            i = m.end()
        else:
            i += 1
    return tokens
