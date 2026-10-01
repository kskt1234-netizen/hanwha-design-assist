from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClient(Protocol):
    provider: str
    model: str

    def generate(self, task: str, system: str, prompt: str, schema: type[T], context: dict[str, Any]) -> T:
        """schema 에 맞는 구조화 결과를 돌려준다.

        task: 단계 이름 (requirements|features|data_model|review)
        system, prompt: 실제 LLM에 보낼 지시문과 입력
        context: 프롬프트를 만든 원재료 (Mock 구현이 문자열 파싱 없이 쓰도록 함께 전달)
        실제 공급자 구현은 tool use / JSON schema 강제 출력으로 schema.model_json_schema() 를 넘기고
        응답을 schema.model_validate() 로 검증하면 된다.
        """
        ...


class LLMNotConfigured(RuntimeError):
    pass
