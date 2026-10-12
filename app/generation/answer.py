"""AnswerGenerator：编排 提示词 → LLM 调用 → 引用解析 → 拒答判定 → 结果组装。

引用解析与拒答判定均基于 MockClient 可完整离线测试，不依赖真实 API。
"""

from __future__ import annotations

import re
import time
from typing import Iterable, Optional, Sequence

from pydantic import BaseModel, Field

from app.generation.llm import LLMClient, LLMResponse
from app.generation.prompt import (
    HitLike,
    REFUSAL_ANSWER,
    build_context,
    build_messages,
)

__all__ = ["AnswerGenerator", "GenerationResult"]


class GenerationResult(BaseModel):
    """generate() 的结构化结果。cited_chunks 为引用解析得到的 chunk_id 列表。"""

    answer: str
    cited_chunks: list[str] = Field(default_factory=list)
    refusal: bool = False
    model: str = ""
    usage: dict = Field(default_factory=dict)
    latency_ms: int = 0
    request_id: str = ""
    citation_parse_warning: Optional[str] = None


#: 回答中【E{n}] 引用标记（全角方括号），n 为 1..len(hits)。
_CITATION_RE = re.compile(r"【E(\d+)】")
#: 中文段兜底归一化：假名 / 括号组 / 纯读法括号判定
_ZH_MARKER = "【中文】"
_KANA_RE = re.compile(r"[\u3040-\u309f\u30a0-\u30ff]+")
_PAREN_RE = re.compile(r"（[^（）]*）")
_PURE_READING_RE = re.compile(r"^[\u3040-\u309f\u30a0-\u30ff\u30fc\u30fb\s]*$")
#: 日文新字体→简体（仅作用于中文段括号外；括号内日文原词保持原样交给前端标注）
_SHINJITAI_MAP = str.maketrans({
    "動": "动", "監": "监", "絵": "绘", "検": "检", "進": "进",
    "図": "图", "済": "济", "対": "对", "変": "变", "価": "价",
    "処": "处", "両": "两", "単": "单", "営": "营", "術": "术",
    "録": "录", "様": "样", "権": "权", "団": "团", "圧": "压",
})
#: 明确拒答开头词（strip 后 startswith 判定）。
_REFUSAL_PREFIXES = (
    "证据不足",
    "无法从知识库回答",
    "不知道",
    "抱歉",
    "对不起",
)


class AnswerGenerator:
    """基于检索证据的问答生成器。

    拒答判定（满足其一即 refusal=True）：
    1. 回答包含标准拒答话术「证据不足」；
    2. 回答 strip 后以明确拒答词开头（不知道 / 抱歉 / 对不起 等）。
    """

    def __init__(self, client: LLMClient) -> None:
        self.client = client

    # ------------------------------------------------------------------ #
    # 内部工具
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_citations(answer: str) -> list[int]:
        """提取回答中的 E 编号（1-based），去重并保持出现顺序。"""
        seen: dict[int, None] = {}
        for m in _CITATION_RE.finditer(answer or ""):
            num = int(m.group(1))
            seen.setdefault(num, None)
        return list(seen)

    @classmethod
    def is_refusal(cls, answer: str) -> bool:
        """拒答判定：含「证据不足」或以明确拒答词开头。"""
        text = (answer or "").strip()
        if not text:
            return True
        if REFUSAL_ANSWER[:4] in text:  # 「证据不足」
            return True
        return any(text.startswith(p) for p in _REFUSAL_PREFIXES)

    @staticmethod
    def normalize_zh_section(answer: str) -> str:
        """中文段行文兜底（提示词对弱模型不可靠，代码层保证）。

        仅处理「【中文】」标记之后的内容：
        1. 纯假名读法括号组（如（げんが））整组删除；
        2. 含汉字的括号组（如（動画チェック））视为日文术语原词，保留；
        3. 括号外：删除残留假名（は/です 等），日文新字体映射回简体，
           日式顿号「、」改中文逗号。
        无「【中文】」标记（单语回答）不做任何处理。
        """
        if _ZH_MARKER not in (answer or ""):
            return answer
        head, _, zh = answer.partition(_ZH_MARKER)
        out: list[str] = []
        pos = 0
        for m in _PAREN_RE.finditer(zh):
            outside = zh[pos:m.start()]
            outside = _KANA_RE.sub("", outside)
            outside = outside.translate(_SHINJITAI_MAP)
            outside = outside.replace("、", "，")
            out.append(outside)
            inner = m.group(0)[1:-1]
            if not _PURE_READING_RE.match(inner):
                out.append(m.group(0))  # 日文术语原词括号，原文保留
            # 纯假名读法括号：整组丢弃
            pos = m.end()
        tail = zh[pos:]
        tail = _KANA_RE.sub("", tail)
        tail = tail.translate(_SHINJITAI_MAP)
        tail = tail.replace("、", "，")
        out.append(tail)
        return head + _ZH_MARKER + "".join(out)

    # ------------------------------------------------------------------ #
    # 主流程
    # ------------------------------------------------------------------ #

    def generate(
        self,
        question: str,
        hits: Sequence[HitLike],
        timeout: Optional[float] = None,
    ) -> GenerationResult:
        """基于检索命中块生成回答并解析引用。

        - 引用【E{n}】映射回 hits[n-1].chunk_id；
        - 引用了不存在的 E 编号（越界）时设置 ``citation_parse_warning``；
        - 不调用真实 API（client 可为 MockClient），超时等异常由 LLMClient 统一抛出。
        """
        context = build_context(hits)
        messages = build_messages(question, context, mode="rag")
        start = time.perf_counter()
        response: LLMResponse = self.client.chat(messages)
        wall_ms = int((time.perf_counter() - start) * 1000)

        answer_text = response.text
        answer_text = self.normalize_zh_section(answer_text)
        refusal = self.is_refusal(answer_text)

        chunk_ids = [getattr(h, "chunk_id", "") for h in hits]
        cited_chunks: list[str] = []
        warnings: list[str] = []
        for num in self._extract_citations(answer_text):
            if 1 <= num <= len(chunk_ids):
                cid = chunk_ids[num - 1]
                if cid not in cited_chunks:
                    cited_chunks.append(cid)
            else:
                warnings.append(f"E{num}")

        citation_parse_warning = None
        if warnings:
            citation_parse_warning = (
                f"回答引用了不存在的证据编号: {', '.join(warnings)}"
                f"（有效范围 E1–E{len(chunk_ids)}）"
            )

        return GenerationResult(
            answer=answer_text,
            cited_chunks=cited_chunks,
            refusal=refusal,
            model=response.model,
            usage=response.usage.model_dump(),
            latency_ms=wall_ms,
            request_id=response.request_id,
            citation_parse_warning=citation_parse_warning,
        )


def format_hits_preview(hits: Iterable[HitLike], limit: int = 3) -> str:
    """调试辅助：打印命中块概览。"""
    lines = []
    for i, h in enumerate(hits, 1):
        if i > limit:
            lines.append("…")
            break
        snippet = (getattr(h, "text_snippet", "") or "")[:60].replace("\n", " ")
        lines.append(f"[E{i}] {getattr(h, 'chunk_id', '?')} | {snippet}")
    return "\n".join(lines)
