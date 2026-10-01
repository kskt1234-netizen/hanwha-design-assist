"""단계별 LLM 프롬프트. 실제 LLM 공급자가 연결되면 이 문자열이 그대로 전달된다."""
import json

from app.rag.retriever import RetrievedChunk
from app.schemas import DesignState, Feature, Requirement

SYSTEM = (
    "당신은 업무 시스템 설계를 돕는 수석 분석가입니다. "
    "주어진 도메인 지식을 우선 참고하고, 근거가 없는 내용은 만들지 마십시오. "
    "반드시 지정된 JSON 스키마로만 답하십시오."
)


def knowledge_block(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "(검색된 도메인 지식 없음)"
    return "\n".join(f"- [{c.type}] {c.title}: {c.content}" for c in chunks)


def requirements_prompt(document_text: str, knowledge: list[RetrievedChunk]) -> str:
    return f"""다음 고객 요구사항 문서를 요구사항 단위로 나누고 기능/비기능으로 분류하십시오.
각 요구사항에 REQ-001 부터 순서대로 코드를 붙이고, 원문 표현을 최대한 유지하십시오.

## 도메인 지식
{knowledge_block(knowledge)}

## 요구사항 문서
{document_text}"""


def features_prompt(requirements: list[Requirement], knowledge: list[RetrievedChunk]) -> str:
    reqs = "\n".join(f"{r.code} [{r.type.value}] {r.text}" for r in requirements)
    return f"""기능 요구사항으로부터 기능 명세를 작성하십시오.
- 기능 코드는 FN-001 부터 순서대로
- 기능명은 '대상 + 동작' 형태의 짧은 명사구 (예: 품목 등록)
- 우선순위는 HIGH/MEDIUM/LOW
- requirement_codes 에 근거 요구사항 코드를 모두 적을 것. 근거 없는 기능은 만들지 말 것

## 도메인 지식
{knowledge_block(knowledge)}

## 요구사항
{reqs}"""


def data_model_prompt(features: list[Feature], knowledge: list[RetrievedChunk]) -> str:
    feats = "\n".join(f"{f.code} {f.name}: {f.description}" for f in features)
    return f"""기능 명세를 구현하는 데 필요한 PostgreSQL 데이터 모델을 도출하십시오.
- 테이블/컬럼은 도메인 명명 규칙을 따를 것
- 모든 테이블에 PK를 둘 것. FK는 relationships 에 from_table(자식)/to_table(부모)/fk_column 으로 적을 것
- N:M 관계는 연결 테이블로 풀 것
- 각 테이블의 feature_codes 에 그 테이블을 쓰는 기능 코드를 적을 것

## 도메인 지식 (엔티티 패턴, 명명 규칙)
{knowledge_block(knowledge)}

## 기능 명세
{feats}"""


def review_prompt(state: DesignState) -> str:
    return f"""다음 설계 산출물을 검토하여 의미상의 문제만 찾으십시오. (형식 오류는 별도 규칙으로 검사함)
- L01: 서로 상충하는 요구사항
- L02: 요구사항에 등장하지만 데이터 모델에 없는 데이터 항목
- L03: 비기능 요구사항(이력 보관, 감사 로그, 보안 등)이 데이터 모델에 반영되지 않음

## 설계 산출물
{json.dumps(state.model_dump(mode="json"), ensure_ascii=False, indent=1)}"""
