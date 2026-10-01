"""설계 파이프라인 단계. 각 단계는 RAG 검색 → LLM 구조화 생성 → 저장 → 실행 기록 순서로 동작한다."""
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app import repository
from app.llm import get_llm
from app.models import GenerationRun, Project, ReviewIssueRow
from app.pipeline import prompts
from app.rag import retriever
from app.review.rules import run_rules
from app.schemas import DataModel, FeatureSpec, LlmReview, RequirementAnalysis, ReviewIssue, Severity


class StageError(ValueError):
    pass


def _log_run(session: Session, project: Project, stage: str, chunk_ids: list[int], error: str | None = None) -> None:
    llm = get_llm()
    session.add(
        GenerationRun(
            project_id=project.id,
            stage=stage,
            provider=llm.provider,
            model=llm.model,
            status="ERROR" if error else "OK",
            error=error,
            retrieved_chunk_ids=chunk_ids,
        )
    )


def _set_status(project: Project, stage: str, status: str) -> None:
    project.stage_status = {**project.stage_status, stage: status}


def generate_requirements(session: Session, project: Project) -> None:
    if not project.documents:
        raise StageError("요구사항 문서를 먼저 업로드하세요.")
    text = "\n\n".join(d.raw_text for d in project.documents)
    knowledge = retriever.search(session, project.domain, text[:2000], types=["term", "rule"])
    result = get_llm().generate(
        "requirements",
        prompts.SYSTEM,
        prompts.requirements_prompt(text, knowledge),
        RequirementAnalysis,
        {"document_text": text, "knowledge": knowledge},
    )
    repository.save_requirements(session, project.id, result.requirements)
    _set_status(project, "requirements", "DRAFT")
    _log_run(session, project, "requirements", [c.id for c in knowledge])
    session.commit()


def generate_features(session: Session, project: Project) -> None:
    state = repository.load_state(session, project.id)
    if not state.requirements:
        raise StageError("요구사항 분석을 먼저 실행하세요.")
    knowledge = retriever.search_many(
        session, project.domain, [r.text for r in state.requirements], types=["term", "rule"], k=3
    )
    result = get_llm().generate(
        "features",
        prompts.SYSTEM,
        prompts.features_prompt(state.requirements, knowledge),
        FeatureSpec,
        {"requirements": state.requirements, "knowledge": knowledge},
    )
    repository.save_features(session, project.id, result.features)
    _set_status(project, "features", "DRAFT")
    _log_run(session, project, "features", [c.id for c in knowledge])
    session.commit()


def generate_data_model(session: Session, project: Project) -> None:
    state = repository.load_state(session, project.id)
    if not state.features:
        raise StageError("기능 명세를 먼저 생성하세요.")
    knowledge = retriever.search_many(
        session, project.domain, [f"{f.name} {f.description}" for f in state.features], types=["pattern"], k=3
    )
    knowledge += retriever.search(session, project.domain, "명명 규칙", types=["naming"], k=1)
    knowledge += retriever.referenced_patterns(session, project.domain, knowledge)
    knowledge = list({c.id: c for c in knowledge}.values())
    result = get_llm().generate(
        "data_model",
        prompts.SYSTEM,
        prompts.data_model_prompt(state.features, knowledge),
        DataModel,
        {"features": state.features, "knowledge": knowledge},
    )
    repository.save_data_model(session, project.id, result.entities, result.relationships)
    _set_status(project, "data_model", "DRAFT")
    _log_run(session, project, "data_model", [c.id for c in knowledge])
    session.commit()


def run_review(session: Session, project: Project) -> list[ReviewIssue]:
    state = repository.load_state(session, project.id)
    issues = run_rules(state, session)
    llm_result = get_llm().generate(
        "review", prompts.SYSTEM, prompts.review_prompt(state), LlmReview, {"state": state}
    )
    issues += [
        ReviewIssue(
            rule_code=f.rule_code,
            severity=Severity.WARN,
            target_type=f.target_type,
            target_code=f.target_code,
            message=f.message,
        )
        for f in llm_result.findings
    ]
    session.execute(delete(ReviewIssueRow).where(ReviewIssueRow.project_id == project.id))
    for i in issues:
        session.add(
            ReviewIssueRow(
                project_id=project.id,
                rule_code=i.rule_code,
                severity=i.severity.value,
                target_type=i.target_type,
                target_code=i.target_code,
                message=i.message,
            )
        )
    _log_run(session, project, "review", [])
    session.commit()
    return issues


GENERATORS = {
    "requirements": generate_requirements,
    "features": generate_features,
    "data_model": generate_data_model,
}
