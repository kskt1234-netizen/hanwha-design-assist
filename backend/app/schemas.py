"""설계 산출물의 구조화 스키마.

LLM은 이 스키마에 맞는 JSON만 생성하고, ERD·DDL·추적표는 이 구조에서 코드로 만든다.
"""
from enum import Enum

from pydantic import BaseModel, Field


class RequirementType(str, Enum):
    FUNCTIONAL = "FUNCTIONAL"
    NON_FUNCTIONAL = "NON_FUNCTIONAL"


class Priority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Cardinality(str, Enum):
    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:N"
    MANY_TO_MANY = "N:M"


class Requirement(BaseModel):
    code: str = Field(description="REQ-001 형식")
    text: str
    type: RequirementType = RequirementType.FUNCTIONAL


class Feature(BaseModel):
    code: str = Field(description="FN-001 형식")
    name: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    requirement_codes: list[str] = Field(default_factory=list)


class Attribute(BaseModel):
    name: str = Field(description="물리 컬럼명 (snake_case)")
    logical_name: str = ""
    data_type: str = Field(default="VARCHAR", description="PostgreSQL 타입")
    length: int | None = None
    nullable: bool = True
    is_pk: bool = False
    is_unique: bool = False
    default: str | None = None


class Entity(BaseModel):
    table_name: str
    logical_name: str = ""
    description: str = ""
    attributes: list[Attribute] = Field(default_factory=list)
    feature_codes: list[str] = Field(default_factory=list)


class Relationship(BaseModel):
    from_table: str = Field(description="FK를 가진 쪽 (자식)")
    to_table: str = Field(description="참조되는 쪽 (부모)")
    fk_column: str
    cardinality: Cardinality = Cardinality.ONE_TO_MANY
    on_delete: str = "RESTRICT"


# ---- 단계별 LLM 출력 스키마 ----

class RequirementAnalysis(BaseModel):
    requirements: list[Requirement]


class FeatureSpec(BaseModel):
    features: list[Feature]


class DataModel(BaseModel):
    entities: list[Entity]
    relationships: list[Relationship] = Field(default_factory=list)


class LlmReviewFinding(BaseModel):
    rule_code: str = Field(description="L01 요구사항 상충, L02 모델 누락 데이터, L03 비기능 미반영")
    target_type: str
    target_code: str
    message: str


class LlmReview(BaseModel):
    findings: list[LlmReviewFinding] = Field(default_factory=list)


# ---- 전체 설계 상태 ----

class DesignState(BaseModel):
    requirements: list[Requirement] = Field(default_factory=list)
    features: list[Feature] = Field(default_factory=list)
    entities: list[Entity] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)


class TraceRow(BaseModel):
    requirement_code: str
    requirement_text: str
    requirement_type: RequirementType
    feature_code: str | None = None
    feature_name: str | None = None
    tables: list[str] = Field(default_factory=list)


class Severity(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"


class ReviewIssue(BaseModel):
    rule_code: str
    severity: Severity
    target_type: str
    target_code: str
    message: str
