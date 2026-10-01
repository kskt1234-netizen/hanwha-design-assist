from app.config import get_settings
from app.llm.base import LLMClient, LLMNotConfigured
from app.llm.mock import MockLLM


def get_llm() -> LLMClient:
    settings = get_settings()
    if settings.llm_provider == "mock":
        return MockLLM()
    # LLM 공급자가 정해지면 app/llm/<provider>.py 에 LLMClient 구현을 추가하고 여기서 연결한다.
    raise LLMNotConfigured(
        f"LLM 공급자 '{settings.llm_provider}' 는 아직 구현되지 않았습니다. APP_LLM_PROVIDER=mock 으로 실행하세요."
    )


__all__ = ["LLMClient", "LLMNotConfigured", "get_llm"]
