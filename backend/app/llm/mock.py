"""규칙 기반 임시 LLM.

LLM 공급자가 정해지기 전까지 API 키 없이 전체 흐름(분석 → 기능 → 데이터 모델 → 검토)을 돌려 보기 위한 구현이다.
품질은 실제 LLM보다 낮지만, 같은 출력 스키마를 지키므로 화면·저장·검토 로직을 그대로 검증할 수 있다.
"""
import re
from typing import Any

from app.llm.base import T
from app.schemas import (
    Attribute,
    DataModel,
    Entity,
    Feature,
    FeatureSpec,
    LlmReview,
    LlmReviewFinding,
    Priority,
    Relationship,
    Requirement,
    RequirementAnalysis,
    RequirementType,
)

NFR_KEYWORDS = ("성능", "응답", "초 이내", "동시", "가용", "보안", "암호", "백업", "보관", "로그", "감사", "호환", "브라우저", "확장")
HIGH_KEYWORDS = ("반드시", "필수", "해야 한다", "되어야 한다")
LOW_KEYWORDS = ("가능하면", "선택", "향후", "추후", "있으면 좋")
ACTIONS = ("등록", "조회", "수정", "삭제", "검색", "관리", "출력", "알림", "승인", "생성", "기록", "처리", "계산", "다운로드", "업로드", "배정", "접수")

_BULLET = re.compile(r"^\s*(?:[-*•·]|\d+[.)]|\(\d+\)|[A-Z]{2,5}-\d+[.:)]?)\s*")
_TRAILING = re.compile(r"\s*(?:할 수 있어야 한다|할 수 있다|해야 한다|되어야 한다|한다|된다)\.?\s*$")


def split_requirements(text: str) -> list[str]:
    items: list[str] = []
    lines = [raw.strip() for raw in text.splitlines()]
    # 목록 형식 문서라면 개요 같은 서술 문단은 요구사항에서 뺀다
    listed = any(_BULLET.match(line) and line[:1] not in "#" for line in lines if line)
    for line in lines:
        if not line or line.startswith("#") or line.endswith(":"):
            continue
        if listed and not _BULLET.match(line):
            continue
        line = _BULLET.sub("", line).strip()
        if len(line) < 8:
            continue
        # 한 줄에 여러 문장이 있으면 나눈다
        for sentence in re.split(r"(?<=다\.)\s+", line):
            sentence = sentence.strip()
            if len(sentence) >= 8:
                items.append(sentence)
    return items


def strip_actor(text: str) -> str:
    """'관리자는 품목을 등록한다' -> '품목을 등록한다'. 행위자는 기능명·테이블 매칭에서 뺀다."""
    return re.sub(r"^\S+[은는]\s+", "", text.strip())


def feature_name(text: str) -> str:
    core = strip_actor(_TRAILING.sub("", text).strip().rstrip("."))
    for action in ACTIONS:
        idx = core.find(action)
        if idx > 0:
            # 동작어 앞의 목적어 구를 붙인다: "품목 정보를 등록" -> "품목 정보 등록"
            head = re.sub(r"[을를이가은는의에]\s*$", "", core[:idx].strip())
            head = head.split(",")[-1].strip()
            words = head.split()[-3:]
            return " ".join(words + [action])
    return core[:30]


class MockLLM:
    provider = "mock"
    model = "rule-based"

    def generate(self, task: str, system: str, prompt: str, schema: type[T], context: dict[str, Any]) -> T:
        handler = getattr(self, f"_{task}")
        result = handler(context)
        return schema.model_validate(result.model_dump())

    def _requirements(self, ctx: dict[str, Any]) -> RequirementAnalysis:
        reqs = []
        for i, sentence in enumerate(split_requirements(ctx["document_text"]), start=1):
            is_nfr = any(k in sentence for k in NFR_KEYWORDS)
            reqs.append(
                Requirement(
                    code=f"REQ-{i:03d}",
                    text=sentence,
                    type=RequirementType.NON_FUNCTIONAL if is_nfr else RequirementType.FUNCTIONAL,
                )
            )
        return RequirementAnalysis(requirements=reqs)

    def _features(self, ctx: dict[str, Any]) -> FeatureSpec:
        features = []
        seen: dict[str, Feature] = {}
        for req in ctx["requirements"]:
            if req.type != RequirementType.FUNCTIONAL:
                continue
            name = feature_name(req.text)
            if name in seen:
                seen[name].requirement_codes.append(req.code)
                continue
            if any(k in req.text for k in HIGH_KEYWORDS):
                priority = Priority.HIGH
            elif any(k in req.text for k in LOW_KEYWORDS):
                priority = Priority.LOW
            else:
                priority = Priority.MEDIUM
            f = Feature(
                code=f"FN-{len(features) + 1:03d}",
                name=name,
                description=req.text,
                priority=priority,
                requirement_codes=[req.code],
            )
            seen[name] = f
            features.append(f)
        return FeatureSpec(features=features)

    def _data_model(self, ctx: dict[str, Any]) -> DataModel:
        patterns = {c.payload["table"]: c.payload for c in ctx["knowledge"] if c.type == "pattern" and c.payload}
        used: dict[str, list[str]] = {}
        for f in ctx["features"]:
            text = f"{f.name} {strip_actor(f.description)}"
            for table, p in patterns.items():
                if any(k in text for k in p["keywords"]):
                    used.setdefault(table, []).append(f.code)

        # FK 대상 부모 테이블도 포함한다 (기능 연결이 없으면 검토에서 드러난다)
        queue = list(used)
        while queue:
            table = queue.pop()
            for ref in patterns[table]["references"]:
                if ref["to"] not in used and ref["to"] in patterns:
                    used[ref["to"]] = []
                    queue.append(ref["to"])

        entities, relationships = [], []
        for table, p in patterns.items():
            if table not in used:
                continue
            entities.append(
                Entity(
                    table_name=table,
                    logical_name=p["logical"],
                    attributes=[
                        Attribute(
                            name=a[0], logical_name=a[1], data_type=a[2], length=a[3],
                            nullable=a[4], is_pk=a[5], is_unique=a[6],
                        )
                        for a in p["attributes"]
                    ],
                    feature_codes=used[table],
                )
            )
            for ref in p["references"]:
                if ref["to"] in used:
                    relationships.append(Relationship(from_table=table, to_table=ref["to"], fk_column=ref["fk"]))
        return DataModel(entities=entities, relationships=relationships)

    def _review(self, ctx: dict[str, Any]) -> LlmReview:
        findings = []
        tables = " ".join(e.table_name for e in ctx["state"].entities)
        for req in ctx["state"].requirements:
            if req.type == RequirementType.NON_FUNCTIONAL and any(k in req.text for k in ("이력", "로그", "감사")):
                if not re.search(r"history|log|transaction|report|result", tables):
                    findings.append(
                        LlmReviewFinding(
                            rule_code="L03",
                            target_type="requirement",
                            target_code=req.code,
                            message="이력·로그 보관 요구가 있지만 이를 저장할 이력 테이블이 데이터 모델에 없습니다.",
                        )
                    )
        return LlmReview(findings=findings)
