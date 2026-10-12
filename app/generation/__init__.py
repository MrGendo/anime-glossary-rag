"""生成层：提示词构建、LLM 客户端（真 + Mock）、引用解析与拒答判定。"""

from app.generation.answer import AnswerGenerator, GenerationResult
from app.generation.llm import (
    ErrorCategory,
    LLMClient,
    LLMConfigError,
    LLMError,
    LLMResponse,
    MockClient,
    ZhipuClient,
)
from app.generation.prompt import (
    NO_RAG_PROMPT,
    REFUSAL_ANSWER,
    SYSTEM_PROMPT_RAG,
    build_context,
    build_messages,
)

__all__ = [
    "NO_RAG_PROMPT",
    "REFUSAL_ANSWER",
    "SYSTEM_PROMPT_RAG",
    "AnswerGenerator",
    "ErrorCategory",
    "GenerationResult",
    "LLMClient",
    "LLMConfigError",
    "LLMError",
    "LLMResponse",
    "MockClient",
    "ZhipuClient",
    "build_context",
    "build_messages",
]
