"""규칙 기반 설계 검토 (R01~R09). 의미 판단이 필요한 검토(L01~L03)는 LLM 단계에서 한다."""
import re
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.generators.ddl import generate_ddl
from app.schemas import Cardinality, DesignState, RequirementType, ReviewIssue, Severity

SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")
# PostgreSQL 예약어 중 테이블/컬럼명으로 자주 실수하는 것
RESERVED = {
    "user", "order", "group", "table", "select", "from", "where", "check", "column", "default",
    "primary", "references", "limit", "offset", "desc", "asc", "end", "case", "when", "to", "all",
}


def _issue(code: str, sev: Severity, ttype: str, target: str, msg: str) -> ReviewIssue:
    return ReviewIssue(rule_code=code, severity=sev, target_type=ttype, target_code=target, message=msg)


def check_traceability(state: DesignState) -> list[ReviewIssue]:
    issues = []
    req_codes = {r.code for r in state.requirements}
    covered = {c for f in state.features for c in f.requirement_codes}
    feature_codes = {f.code for f in state.features}
    used_features = {c for e in state.entities for c in e.feature_codes}

    if state.features:
        for r in state.requirements:
            if r.type == RequirementType.FUNCTIONAL and r.code not in covered:
                issues.append(_issue("R01", Severity.ERROR, "requirement", r.code,
                                     f"기능 요구사항 '{r.text[:40]}'을(를) 구현하는 기능이 없습니다."))
    for f in state.features:
        if not f.requirement_codes:
            issues.append(_issue("R02", Severity.WARN, "feature", f.code, f"기능 '{f.name}'의 근거 요구사항이 없습니다."))
        for c in f.requirement_codes:
            if c not in req_codes:
                issues.append(_issue("R02", Severity.ERROR, "feature", f.code,
                                     f"기능 '{f.name}'이(가) 존재하지 않는 요구사항 {c}을(를) 참조합니다."))
    if state.entities:
        for f in state.features:
            if f.code not in used_features:
                issues.append(_issue("R03", Severity.WARN, "feature", f.code,
                                     f"기능 '{f.name}'이(가) 사용하는 테이블이 없습니다."))
    for e in state.entities:
        if not e.feature_codes:
            issues.append(_issue("R04", Severity.INFO, "entity", e.table_name,
                                 f"테이블 {e.table_name}을(를) 사용하는 기능이 없습니다. (참조용 마스터라면 무시 가능)"))
        for c in e.feature_codes:
            if c not in feature_codes:
                issues.append(_issue("R04", Severity.ERROR, "entity", e.table_name,
                                     f"테이블 {e.table_name}이(가) 존재하지 않는 기능 {c}을(를) 참조합니다."))
    return issues


def check_model_format(state: DesignState) -> list[ReviewIssue]:
    issues = []
    seen_tables: set[str] = set()
    entities = {e.table_name: e for e in state.entities}
    for e in state.entities:
        if e.table_name in seen_tables:
            issues.append(_issue("R05", Severity.ERROR, "entity", e.table_name, f"테이블명 {e.table_name}이(가) 중복됩니다."))
        seen_tables.add(e.table_name)
        if not any(a.is_pk for a in e.attributes):
            issues.append(_issue("R05", Severity.ERROR, "entity", e.table_name, f"테이블 {e.table_name}에 PK가 없습니다."))
        names = [a.name for a in e.attributes]
        for dup in sorted({n for n in names if names.count(n) > 1}):
            issues.append(_issue("R05", Severity.ERROR, "entity", e.table_name, f"{e.table_name}.{dup} 컬럼이 중복됩니다."))
        for n in [e.table_name, *names]:
            if n.lower() in RESERVED:
                issues.append(_issue("R05", Severity.ERROR, "entity", e.table_name, f"'{n}'은(는) PostgreSQL 예약어입니다."))
            if not SNAKE.match(n):
                issues.append(_issue("R08", Severity.WARN, "entity", e.table_name,
                                     f"'{n}'이(가) 명명 규칙(소문자 snake_case)에 맞지 않습니다."))

    for r in state.relationships:
        target = f"{r.from_table}.{r.fk_column}"
        if r.cardinality == Cardinality.MANY_TO_MANY:
            issues.append(_issue("R07", Severity.ERROR, "relationship", target,
                                 f"{r.from_table}–{r.to_table} N:M 관계는 연결 테이블로 풀어야 합니다."))
        child, parent = entities.get(r.from_table), entities.get(r.to_table)
        if not child or not parent:
            missing = r.from_table if not child else r.to_table
            issues.append(_issue("R06", Severity.ERROR, "relationship", target, f"관계가 존재하지 않는 테이블 {missing}을(를) 참조합니다."))
            continue
        fk = next((a for a in child.attributes if a.name == r.fk_column), None)
        if not fk:
            issues.append(_issue("R06", Severity.ERROR, "relationship", target, f"FK 컬럼 {target}이(가) 없습니다."))
            continue
        pks = [a for a in parent.attributes if a.is_pk]
        if len(pks) == 1 and pks[0].data_type.upper() != fk.data_type.upper():
            issues.append(_issue("R06", Severity.ERROR, "relationship", target,
                                 f"FK {target}({fk.data_type})와 {r.to_table}.{pks[0].name}({pks[0].data_type}) 타입이 다릅니다."))
    return issues


def check_ddl_executes(state: DesignState, session: Session) -> list[ReviewIssue]:
    """생성 DDL을 임시 스키마에서 실제로 실행해 보고 롤백한다."""
    if not state.entities:
        return []
    schema = f"ddl_check_{uuid.uuid4().hex[:8]}"
    conn = session.connection()
    tx = conn.begin_nested()
    try:
        conn.execute(text(f"CREATE SCHEMA {schema}"))
        conn.execute(text(f"SET LOCAL search_path TO {schema}"))
        conn.exec_driver_sql(generate_ddl(state))
        return []
    except Exception as exc:  # noqa: BLE001
        msg = str(getattr(exc, "orig", exc)).splitlines()[0]
        return [_issue("R09", Severity.ERROR, "ddl", "DDL", f"DDL 실행 실패: {msg}")]
    finally:
        tx.rollback()
        conn.execute(text("SET search_path TO public"))


def run_rules(state: DesignState, session: Session | None = None) -> list[ReviewIssue]:
    issues = check_traceability(state) + check_model_format(state)
    if session is not None:
        issues += check_ddl_executes(state, session)
    return issues
