"""LLM 客户端：真实 Zhipu（OpenAI 兼容）客户端 + 测试用 Mock 客户端。

设计要点
--------
- 统一结构化返回 ``LLMResponse``：text / model / usage / latency_ms / finish_reason / request_id。
- 统一异常 ``LLMError``，携带 ``category``（timeout / rate_limit / other）与 ``retryable``。
- 指数退避重试（默认 2 次），仅对超时、限流这类瞬态错误重试。
- API key 只从环境变量 ``ZHIPU_API_KEY`` 读取，绝不写入代码、异常消息或日志。
"""

from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Literal, Optional, Sequence

from pydantic import BaseModel, Field

__all__ = [
    "ErrorCategory",
    "LLMClient",
    "LLMConfigError",
    "LLMError",
    "LLMResponse",
    "LLMUsage",
    "MockClient",
    "MockMode",
    "ZhipuClient",
]


class ErrorCategory(str, Enum):
    """LLM 调用失败的分类：超时 / 限流 / 其他。"""

    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    OTHER = "other"


# 仅瞬态错误进入重试：超时、限流。参数错误等 OTHER 类直接抛出。
_RETRYABLE_CATEGORIES = {ErrorCategory.TIMEOUT, ErrorCategory.RATE_LIMIT}


class LLMError(Exception):
    """LLM 调用失败。``category`` 用于异常分类，``retryable`` 决定是否退避重试。"""

    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.OTHER) -> None:
        super().__init__(message)
        self.category = category
        self.retryable = category in _RETRYABLE_CATEGORIES


class LLMConfigError(RuntimeError):
    """客户端构造期配置错误（如缺少 API key）。不属于调用期错误，不参与重试。"""


class LLMUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0


class LLMResponse(BaseModel):
    """结构化返回。latency_ms 为单次成功调用的耗时（不含重试等待）。"""

    text: str
    model: str
    usage: LLMUsage = Field(default_factory=LLMUsage)
    latency_ms: int = 0
    finish_reason: str = "stop"
    request_id: str = ""


class LLMClient(ABC):
    """LLM 客户端基类：模板方法统一处理重试与异常分类，子类只实现单次调用。"""

    def __init__(
        self,
        model: str,
        timeout: float = 30.0,
        max_retries: int = 2,
        retry_base_delay: float = 1.0,
    ) -> None:
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay

    @abstractmethod
    def _chat_once(self, messages: Sequence[Dict[str, str]]) -> LLMResponse:
        """执行一次补全调用；失败时抛出携带 category 的 LLMError。"""

    def chat(self, messages: Sequence[Dict[str, str]]) -> LLMResponse:
        """带指数退避重试的调用入口：重试延迟 = retry_base_delay * 2^attempt。"""
        for attempt in range(self.max_retries + 1):
            try:
                return self._chat_once(list(messages))
            except LLMError as exc:
                if not exc.retryable or attempt >= self.max_retries:
                    raise
                delay = self.retry_base_delay * (2**attempt)
                if delay > 0:
                    time.sleep(delay)
        raise AssertionError("unreachable")  # pragma: no cover


class ZhipuClient(LLMClient):
    """智谱 OpenAI 兼容客户端（默认 glm-4-flash，免费档）。

    API key 仅从环境变量 ``ZHIPU_API_KEY``（或显式入参）读取；缺失时构造即抛
    ``LLMConfigError``。任何日志与异常消息都不包含 key。
    """

    BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
    DEFAULT_MODEL = "glm-4-flash"
    ENV_API_KEY = "ZHIPU_API_KEY"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: float = 30.0,
        max_retries: int = 2,
        retry_base_delay: float = 1.0,
        temperature: float = 0.2,
    ) -> None:
        super().__init__(
            model=model,
            timeout=timeout,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
        )
        resolved = api_key if api_key is not None else os.environ.get(self.ENV_API_KEY)
        resolved = (resolved or "").strip()
        if not resolved:
            raise LLMConfigError(
                f"缺少智谱 API key：请先设置环境变量 {self.ENV_API_KEY}"
                f"（例如 export {self.ENV_API_KEY}=<你的key>），再构造 ZhipuClient。"
            )
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - 环境缺依赖时给出可操作提示
            raise LLMConfigError(
                "未安装 openai 依赖：uv pip install --python .venv/bin/python openai"
            ) from exc
        # 重试由本基类统一控制，关闭 SDK 内建重试避免叠加。
        self._client = OpenAI(
            api_key=resolved,
            base_url=self.BASE_URL,
            timeout=self.timeout,
            max_retries=0,
        )
        self.temperature = temperature

    def _chat_once(self, messages: Sequence[Dict[str, str]]) -> LLMResponse:
        start = time.perf_counter()
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=list(messages),
                temperature=self.temperature,
                timeout=self.timeout,
            )
        except Exception as exc:
            raise self._classify_and_wrap(exc) from exc
        latency_ms = int((time.perf_counter() - start) * 1000)
        choice = resp.choices[0] if resp.choices else None
        text = (choice.message.content or "") if choice else ""
        finish_reason = (getattr(choice, "finish_reason", None) if choice else None) or "stop"
        usage = getattr(resp, "usage", None)
        return LLMResponse(
            text=text,
            model=getattr(resp, "model", None) or self.model,
            usage=LLMUsage(
                prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            ),
            latency_ms=latency_ms,
            finish_reason=str(finish_reason),
            request_id=str(getattr(resp, "id", "") or ""),
        )

    @staticmethod
    def _classify_and_wrap(exc: Exception) -> LLMError:
        """把 openai SDK 异常映射为带分类的 LLMError；消息只含类型与描述，不含 key。"""
        category = ErrorCategory.OTHER
        try:
            from openai import APITimeoutError, InternalServerError, RateLimitError

            if isinstance(exc, APITimeoutError):
                category = ErrorCategory.TIMEOUT
            elif isinstance(exc, RateLimitError):
                category = ErrorCategory.RATE_LIMIT
            elif isinstance(exc, InternalServerError):
                # provider 5xx: transient -> retryable via backoff
                category = ErrorCategory.RATE_LIMIT
        except ImportError:  # pragma: no cover
            pass
        return LLMError(f"{type(exc).__name__}: {exc}", category=category)


MockMode = Literal["answer", "refusal", "timeout"]

DEFAULT_MOCK_ANSWER = (
    "作画监督（作画監督）是统一单集作画质量与角色演技的关键职位【E1】；"
    "在跨话项目中还会配置总作画监督对整体作画把关【E2】。"
)
DEFAULT_MOCK_REFUSAL = "证据不足，无法从知识库回答。"


class MockClient(LLMClient):
    """测试用 Mock 客户端，不访问网络。

    mode:
      - "answer": 返回固定答案（answer_text，默认含【E1】【E2】引用）
      - "refusal": 返回固定拒答（refusal_text）
      - "timeout": 每次调用抛出分类为 timeout 的 LLMError（用于验证重试与异常分类）
    """

    _VALID_MODES = ("answer", "refusal", "timeout")

    def __init__(
        self,
        mode: str = "answer",
        answer_text: str = DEFAULT_MOCK_ANSWER,
        refusal_text: str = DEFAULT_MOCK_REFUSAL,
        model: str = "mock-llm",
        timeout: float = 30.0,
        max_retries: int = 2,
        retry_base_delay: float = 1.0,
    ) -> None:
        super().__init__(
            model=model,
            timeout=timeout,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
        )
        if mode not in self._VALID_MODES:
            raise ValueError(f"未知 MockClient mode: {mode!r}，可选 {self._VALID_MODES}")
        self.mode = mode
        self.answer_text = answer_text
        self.refusal_text = refusal_text
        # 记录每次尝试的入参，供测试断言重试次数与消息结构。
        self.calls: list = []

    @property
    def call_count(self) -> int:
        return len(self.calls)

    def _chat_once(self, messages: Sequence[Dict[str, str]]) -> LLMResponse:
        self.calls.append([dict(m) for m in messages])
        if self.mode == "timeout":
            raise LLMError("MockClient: 模拟请求超时", category=ErrorCategory.TIMEOUT)
        text = self.refusal_text if self.mode == "refusal" else self.answer_text
        prompt_tokens = sum(len(m.get("content", "")) for m in messages)
        return LLMResponse(
            text=text,
            model=self.model,
            usage=LLMUsage(prompt_tokens=prompt_tokens, completion_tokens=len(text)),
            latency_ms=0,
            finish_reason="stop",
            request_id=f"mock-{len(self.calls)}",
        )
