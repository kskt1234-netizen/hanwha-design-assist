# AI 설계 지원 서비스 (과제 8)

고객 요구사항 문서를 넣으면 요구사항 분석 → 기능 명세서 → 데이터 모델(ERD·DDL) → 추적표 → 설계 검토까지 초안을 만들고, 사용자가 단계마다 수정·승인하는 웹 서비스의 뼈대입니다.
설계 근거는 [../architecture/architecture-proposal.md](../architecture/architecture-proposal.md) 에 있습니다.

## 현재 상태

| 영역 | 상태 |
|---|---|
| 백엔드 (FastAPI) | 프로젝트·문서·단계 생성/편집/승인·추적표·검토·DDL/Mermaid 내보내기 API 동작 |
| DB (PostgreSQL + pgvector) | 산출물 정규화 테이블, 승인 버전 스냅샷(JSONB), 도메인 지식 벡터 |
| LLM | **미정.** `MockLLM` (규칙 기반 임시 구현)으로 키 없이 전체 흐름이 돈다. 프롬프트(`app/pipeline/prompts.py`)는 실제 LLM용으로 작성돼 있음 |
| 임베딩 | **미정.** 문자 n-gram 해싱 임시 구현 (`app/rag/embedder.py`) |
| 도메인 지식 | 재고관리, 설비관리 (`backend/knowledge/*.json`: 용어·업무규칙·명명규칙·엔티티 패턴) |
| 검토 규칙 | R01~R09 규칙 검사 (DDL은 임시 스키마에서 실제 실행 후 롤백), L01~L03은 LLM 단계 (Mock은 L03만 흉내) |
| 프론트엔드 (React + Vite + Ant Design) | 문서 입력, 요구사항/기능/데이터 모델 편집·승인, ERD(Mermaid)·DDL 보기, 추적표, 검토 결과 |

## 실행

### Docker
```bash
docker compose up --build
# http://localhost:5173
```

### 직접 실행
```bash
# 1) PostgreSQL 16 + pgvector, DB/사용자 design/design
# 2) 백엔드
cd backend
pip install -r requirements.txt
cp .env.example .env
python -m app.seed                 # 도메인 지식 적재
uvicorn app.main:app --reload      # http://localhost:8000/docs
# 3) 프론트엔드
cd ../frontend
npm install
npm run dev                        # http://localhost:5173 (/api 는 8000으로 프록시)
```

### 테스트
```bash
cd backend
createdb -U design design_test     # 테스트 전용 DB
pytest
```

## 구조

```
backend/app/
  main.py              REST API
  models.py            DB 테이블 (project, requirement, feature, entity, attribute, relationship,
                       trace_link, review_issue, artifact_version, generation_run, knowledge_chunk)
  schemas.py           LLM 출력 및 설계 상태 스키마 (Pydantic)
  repository.py        정규화 테이블 <-> DesignState
  pipeline/stages.py   단계 실행: RAG 검색 → LLM 구조화 생성 → 저장 → 실행 기록
  pipeline/prompts.py  단계별 프롬프트
  llm/                 LLMClient 인터페이스, MockLLM
  rag/                 임베딩, pgvector 검색, 지식 적재
  generators/          DDL(PostgreSQL), Mermaid ERD, 추적표
  review/rules.py      규칙 검토 R01~R09
backend/knowledge/     도메인 지식 JSON
frontend/src/          화면
samples/               가상 요구사항 정의서 (재고관리, 설비관리)
```

## LLM 공급자가 정해지면

1. `app/llm/<공급자>.py` 에 `LLMClient.generate()` 구현: tool use 또는 JSON schema 강제 출력에 `schema.model_json_schema()` 를 넘기고 응답을 `schema.model_validate()` 로 검증
2. `app/llm/__init__.py` 의 `get_llm()` 에 연결
3. `.env` 에 `APP_LLM_PROVIDER`, `APP_LLM_MODEL`, `APP_LLM_API_KEY` 설정

임베딩 모델을 바꾸면 `APP_EMBEDDING_DIM` 을 맞추고 `knowledge_chunk` 테이블을 다시 만든 뒤 `python -m app.seed` 를 실행합니다.
