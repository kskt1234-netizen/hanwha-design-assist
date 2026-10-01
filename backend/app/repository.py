"""정규화 테이블 <-> DesignState 변환."""
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    AttributeRow,
    EntityRow,
    FeatureRow,
    RelationshipRow,
    RequirementRow,
    TraceLink,
)
from app.schemas import Attribute, DesignState, Entity, Feature, Relationship, Requirement


def load_state(session: Session, project_id: int) -> DesignState:
    reqs = session.scalars(
        select(RequirementRow).where(RequirementRow.project_id == project_id).order_by(RequirementRow.seq)
    ).all()
    feats = session.scalars(
        select(FeatureRow).where(FeatureRow.project_id == project_id).order_by(FeatureRow.seq)
    ).all()
    ents = session.scalars(
        select(EntityRow).where(EntityRow.project_id == project_id).order_by(EntityRow.seq)
    ).all()
    rels = session.scalars(
        select(RelationshipRow).where(RelationshipRow.project_id == project_id).order_by(RelationshipRow.id)
    ).all()
    links = session.scalars(select(TraceLink).where(TraceLink.project_id == project_id)).all()

    req_by_feature: dict[str, list[str]] = {}
    features_by_table: dict[str, list[str]] = {}
    for link in links:
        if link.requirement_code:
            req_by_feature.setdefault(link.feature_code, []).append(link.requirement_code)
        if link.table_name:
            features_by_table.setdefault(link.table_name, []).append(link.feature_code)

    return DesignState(
        requirements=[Requirement(code=r.code, text=r.text, type=r.type) for r in reqs],
        features=[
            Feature(
                code=f.code,
                name=f.name,
                description=f.description,
                priority=f.priority,
                requirement_codes=sorted(req_by_feature.get(f.code, [])),
            )
            for f in feats
        ],
        entities=[
            Entity(
                table_name=e.table_name,
                logical_name=e.logical_name,
                description=e.description,
                feature_codes=sorted(features_by_table.get(e.table_name, [])),
                attributes=[
                    Attribute(
                        name=a.name,
                        logical_name=a.logical_name,
                        data_type=a.data_type,
                        length=a.length,
                        nullable=a.nullable,
                        is_pk=a.is_pk,
                        is_unique=a.is_unique,
                        default=a.default,
                    )
                    for a in e.attributes
                ],
            )
            for e in ents
        ],
        relationships=[
            Relationship(
                from_table=r.from_table,
                to_table=r.to_table,
                fk_column=r.fk_column,
                cardinality=r.cardinality,
                on_delete=r.on_delete,
            )
            for r in rels
        ],
    )


def save_requirements(session: Session, project_id: int, requirements: list[Requirement]) -> None:
    session.execute(delete(RequirementRow).where(RequirementRow.project_id == project_id))
    for i, r in enumerate(requirements):
        session.add(RequirementRow(project_id=project_id, code=r.code, text=r.text, type=r.type.value, seq=i))


def save_features(session: Session, project_id: int, features: list[Feature]) -> None:
    session.execute(delete(FeatureRow).where(FeatureRow.project_id == project_id))
    session.execute(
        delete(TraceLink).where(TraceLink.project_id == project_id, TraceLink.requirement_code.is_not(None))
    )
    for i, f in enumerate(features):
        session.add(
            FeatureRow(
                project_id=project_id,
                code=f.code,
                name=f.name,
                description=f.description,
                priority=f.priority.value,
                seq=i,
            )
        )
        for req_code in dict.fromkeys(f.requirement_codes):
            session.add(TraceLink(project_id=project_id, requirement_code=req_code, feature_code=f.code))


def save_data_model(
    session: Session, project_id: int, entities: list[Entity], relationships: list[Relationship]
) -> None:
    for e in session.scalars(select(EntityRow).where(EntityRow.project_id == project_id)):
        session.delete(e)
    session.execute(delete(RelationshipRow).where(RelationshipRow.project_id == project_id))
    session.execute(delete(TraceLink).where(TraceLink.project_id == project_id, TraceLink.table_name.is_not(None)))
    session.flush()
    for i, e in enumerate(entities):
        row = EntityRow(
            project_id=project_id,
            table_name=e.table_name,
            logical_name=e.logical_name,
            description=e.description,
            seq=i,
        )
        row.attributes = [
            AttributeRow(
                name=a.name,
                logical_name=a.logical_name,
                data_type=a.data_type,
                length=a.length,
                nullable=a.nullable,
                is_pk=a.is_pk,
                is_unique=a.is_unique,
                default=a.default,
                seq=j,
            )
            for j, a in enumerate(e.attributes)
        ]
        session.add(row)
        for fn_code in dict.fromkeys(e.feature_codes):
            session.add(TraceLink(project_id=project_id, feature_code=fn_code, table_name=e.table_name))
    for r in relationships:
        session.add(
            RelationshipRow(
                project_id=project_id,
                from_table=r.from_table,
                to_table=r.to_table,
                fk_column=r.fk_column,
                cardinality=r.cardinality.value,
                on_delete=r.on_delete,
            )
        )
