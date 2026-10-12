# -*- coding: utf-8 -*-
"""Demo (no-API-key) LLM client: extractive answering from retrieved evidence.

Instead of a canned answer (which misleads users into thinking the model
answered), this client builds its response FROM the evidence blocks actually
retrieved: it picks the most relevant sentence(s) and cites them with [E#]
labels. Every question therefore gets a different, traceable answer, and the
refusal path is exercised for real (no evidence -> refuse).
"""
from __future__ import annotations

import re
from typing import Dict, List, Sequence

from app.generation.llm import LLMClient, LLMResponse, LLMUsage

EVIDENCE_MARK = "[E"


class ExtractiveDemoClient(LLMClient):
    """Pulls the user question out of the last message, scans the evidence
    context for the best-matching block, returns an extractive answer."""

    def __init__(self):
        super().__init__(model="demo-extractive", timeout=5.0)
        self.calls: list = []

    def _chat_once(self, messages: Sequence[Dict[str, str]]) -> LLMResponse:
        self.calls.append([dict(m) for m in messages])
        system = messages[0]["content"] if messages else ""
        user = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user = m.get("content", "")
                break

        # User content: "问题：...\n\n<CONTEXT_HEADER>...[E1]...<CONTEXT_FOOTER>\n\n请仅基于..."
        # Only the region between the context header/footer is evidence; the
        # trailing instruction text also contains 【E#】 literals that must NOT
        # be treated as evidence blocks.
        header_idx = user.find("知识库片段")
        footer_idx = user.rfind("知识库片段结束")
        if footer_idx < 0:
            footer_idx = len(user)
        evidence_region = user[header_idx:footer_idx] if header_idx >= 0 else user[:footer_idx]
        question = user[:header_idx].replace("问题：", "").strip() if header_idx >= 0 else question
        evid_split = re.split(r"(?=\[E\d+\])", evidence_region)
        blocks = [b.strip() for b in evid_split[1:] if b.strip()]

        if not blocks:
            text = "证据不足，无法从知识库回答该问题。（演示模式：未配置 ZHIPU_API_KEY，当前为基于检索证据的抽取式回答，非生成式模型。）"
        else:
            q_terms = self._terms(question)
            best_i = self._pick_block(blocks, q_terms)
            best = blocks[best_i]
            label = re.match(r"\[E\d+\]", best)
            label = label.group(0) if label else f"[E{best_i + 1}]"
            # drop the "[E#] 来源: ... | 章节: ..." provenance line
            body = re.sub(r"^\[E\d+\][^\n]*\n", "", best).strip()
            sents = re.split(r"(?<=[。．\?？!！])", body)
            take = ""
            for s in sents:
                take += s
                if len(take) >= 80:
                    break
            take = take.strip() or body[:100]
            # 【】 form so the citation parser resolves it to a real chunk
            cite_label = "【" + label.strip("[]") + "】"
            text = (f"（演示模式：未配置 API key，以下为检索命中的最相关证据原文，"
                    f"非生成式回答）\n{take} {cite_label}\n\n"
                    f"完整证据与来源见下方检索列表；配置 ZHIPU_API_KEY 后将基于全部证据生成回答。")
        return LLMResponse(
            text=text, model=self.model,
            usage=LLMUsage(prompt_tokens=sum(len(m.get("content", "")) for m in messages),
                           completion_tokens=len(text)),
            latency_ms=0, finish_reason="stop",
            request_id=f"demo-{len(self.calls)}")

    @staticmethod
    def _pick_block(blocks: List[str], q_terms: List[str]) -> int:
        """Choose the evidence block whose headword (章节: ... line) matches the
        question best; fall back to whole-block term overlap. Glossary entries
        are identified by their headword, and retrieval already ranks by it."""
        best_i, best_score = 0, -1.0
        for i, b in enumerate(blocks):
            m = re.search(r"章节:\s*([^\n|]+)", b)
            head = (m.group(1).strip() if m else "").rstrip("0123456789")
            score = 0.0
            for t in q_terms:
                if len(t) >= 2 and t in head:
                    if head.startswith(t):
                        # exact/prefix match. If the headword is LONGER than the
                        # term it is a sibling entry (レイアウト vs レイアウト撮):
                        # prefer the headword that equals the term length.
                        score += 3.0 if len(head) <= len(t) else 1.5
                    else:
                        score += 1.0
                elif t in b:
                    score += 0.25
            if score > best_score:
                best_i, best_score = i, score
        return best_i

    @staticmethod
    def _terms(q: str) -> List[str]:
        """Simple term extraction: CJK 2-4 grams of the alphabet-free core.
        Question suffixes (とは/です/是什么/是什么意思 etc.) are stripped first
        so they don't glue onto the queried term."""
        q = re.sub(r"(とは|なんですか|是什么意思|是什么|是指|指的是|？|\?)", "", q)
        core = re.sub(r"[^\u3040-\u30ff\u4e00-\u9fffA-Za-z0-9]+", " ", q)
        out = []
        for tok in core.split():
            if len(tok) >= 2:
                out.append(tok)
                if len(tok) > 3:
                    out.extend(tok[i:i + 2] for i in range(len(tok) - 1))
        return out
