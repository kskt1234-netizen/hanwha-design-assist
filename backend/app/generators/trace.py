from app.schemas import DesignState, TraceRow


def build_trace(state: DesignState) -> list[TraceRow]:
    """요구사항 ↔ 기능 ↔ 테이블 추적표. 연결이 없는 요구사항도 빈 행으로 남겨 누락이 보이게 한다."""
    tables_by_feature: dict[str, list[str]] = {}
    for e in state.entities:
        for fn in e.feature_codes:
            tables_by_feature.setdefault(fn, []).append(e.table_name)

    rows: list[TraceRow] = []
    for r in state.requirements:
        linked = [f for f in state.features if r.code in f.requirement_codes]
        if not linked:
            rows.append(TraceRow(requirement_code=r.code, requirement_text=r.text, requirement_type=r.type))
        for f in linked:
            rows.append(
                TraceRow(
                    requirement_code=r.code,
                    requirement_text=r.text,
                    requirement_type=r.type,
                    feature_code=f.code,
                    feature_name=f.name,
                    tables=tables_by_feature.get(f.code, []),
                )
            )
    return rows
