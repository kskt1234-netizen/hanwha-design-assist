from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import get_settings
from app.db import Base

STAGES = ("requirements", "features", "data_model")


class Project(Base):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    domain: Mapped[str] = mapped_column(String(50))
    # {"requirements": "EMPTY|DRAFT|APPROVED", ...}
    stage_status: Mapped[dict] = mapped_column(JSON, default=lambda: {s: "EMPTY" for s in STAGES})
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    documents: Mapped[list["SourceDocument"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class SourceDocument(Base):
    __tablename__ = "source_document"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(300))
    raw_text: Mapped[str] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="documents")


class RequirementRow(Base):
    __tablename__ = "requirement"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(30))
    text: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(20))
    seq: Mapped[int] = mapped_column(Integer)


class FeatureRow(Base):
    __tablename__ = "feature"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(10))
    seq: Mapped[int] = mapped_column(Integer)


class EntityRow(Base):
    __tablename__ = "entity"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    table_name: Mapped[str] = mapped_column(String(100))
    logical_name: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    seq: Mapped[int] = mapped_column(Integer)

    attributes: Mapped[list["AttributeRow"]] = relationship(
        cascade="all, delete-orphan", order_by="AttributeRow.seq"
    )


class AttributeRow(Base):
    __tablename__ = "attribute"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entity.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    logical_name: Mapped[str] = mapped_column(String(200), default="")
    data_type: Mapped[str] = mapped_column(String(50))
    length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nullable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_pk: Mapped[bool] = mapped_column(Boolean, default=False)
    is_unique: Mapped[bool] = mapped_column(Boolean, default=False)
    default: Mapped[str | None] = mapped_column(String(200), nullable=True)
    seq: Mapped[int] = mapped_column(Integer)


class RelationshipRow(Base):
    __tablename__ = "relationship"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    from_table: Mapped[str] = mapped_column(String(100))
    to_table: Mapped[str] = mapped_column(String(100))
    fk_column: Mapped[str] = mapped_column(String(100))
    cardinality: Mapped[str] = mapped_column(String(5))
    on_delete: Mapped[str] = mapped_column(String(20), default="RESTRICT")


class TraceLink(Base):
    """요구사항-기능, 기능-테이블 연결. 한 행은 둘 중 한 종류다."""

    __tablename__ = "trace_link"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    requirement_code: Mapped[str | None] = mapped_column(String(30), nullable=True)
    feature_code: Mapped[str] = mapped_column(String(30))
    table_name: Mapped[str | None] = mapped_column(String(100), nullable=True)


class ReviewIssueRow(Base):
    __tablename__ = "review_issue"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    rule_code: Mapped[str] = mapped_column(String(10))
    severity: Mapped[str] = mapped_column(String(10))
    target_type: Mapped[str] = mapped_column(String(30))
    target_code: Mapped[str] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(10), default="OPEN")  # OPEN|RESOLVED|IGNORED


class ArtifactVersion(Base):
    __tablename__ = "artifact_version"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    stage: Mapped[str] = mapped_column(String(20))
    version_no: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GenerationRun(Base):
    __tablename__ = "generation_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    stage: Mapped[str] = mapped_column(String(20))
    provider: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(100), default="")
    status: Mapped[str] = mapped_column(String(10))  # OK|ERROR
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieved_chunk_ids: Mapped[list] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunk"

    id: Mapped[int] = mapped_column(primary_key=True)
    domain: Mapped[str] = mapped_column(String(50), index=True)
    type: Mapped[str] = mapped_column(String(20))  # term|rule|pattern|naming
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    # pattern 청크의 엔티티 정의 등 구조화 데이터
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    embedding = mapped_column(Vector(get_settings().embedding_dim))
