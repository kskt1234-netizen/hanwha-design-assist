import json
from pathlib import Path

from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import KnowledgeChunk
from app.rag.embedder import get_embedder

KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "knowledge"


class RetrievedChunk(BaseModel):
    id: int
    type: str
    title: str
    content: str
    payload: dict | None = None
    distance: float


def available_domains() -> list[dict]:
    domains = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        domains.append({"code": data["domain"], "name": data["name"]})
    return domains


def seed_knowledge(session: Session) -> int:
    """knowledge/*.json 을 읽어 knowledge_chunk 를 다시 채운다."""
    embedder = get_embedder()
    session.execute(delete(KnowledgeChunk))
    count = 0
    for path in sorted(KNOWLEDGE_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        chunks = data["chunks"]
        vectors = embedder.embed([f"{c['title']} {c['content']}" for c in chunks])
        for c, vec in zip(chunks, vectors):
            session.add(
                KnowledgeChunk(
                    domain=data["domain"],
                    type=c["type"],
                    title=c["title"],
                    content=c["content"],
                    payload=c.get("payload"),
                    embedding=vec,
                )
            )
            count += 1
    session.commit()
    return count


def search(
    session: Session, domain: str, query: str, types: list[str] | None = None, k: int | None = None
) -> list[RetrievedChunk]:
    k = k or get_settings().rag_top_k
    [qvec] = get_embedder().embed([query])
    distance = KnowledgeChunk.embedding.cosine_distance(qvec)
    stmt = select(KnowledgeChunk, distance.label("distance")).where(KnowledgeChunk.domain == domain)
    if types:
        stmt = stmt.where(KnowledgeChunk.type.in_(types))
    rows = session.execute(stmt.order_by(distance).limit(k)).all()
    return [
        RetrievedChunk(
            id=c.id, type=c.type, title=c.title, content=c.content, payload=c.payload, distance=float(d)
        )
        for c, d in rows
    ]


def search_many(
    session: Session, domain: str, queries: list[str], types: list[str] | None = None, k: int | None = None
) -> list[RetrievedChunk]:
    """여러 질의 결과를 합쳐 중복 제거 (거리 짧은 순)."""
    best: dict[int, RetrievedChunk] = {}
    for q in queries:
        for c in search(session, domain, q, types, k):
            if c.id not in best or c.distance < best[c.id].distance:
                best[c.id] = c
    return sorted(best.values(), key=lambda c: c.distance)


def referenced_patterns(session: Session, domain: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """검색된 엔티티 패턴이 FK로 참조하는 부모 테이블 패턴을 (재귀적으로) 가져온다."""
    rows = session.scalars(
        select(KnowledgeChunk).where(KnowledgeChunk.domain == domain, KnowledgeChunk.type == "pattern")
    ).all()
    by_table = {r.payload["table"]: r for r in rows if r.payload}
    have = {c.payload["table"] for c in chunks if c.type == "pattern" and c.payload}
    queue = list(have)
    found: list[RetrievedChunk] = []
    while queue:
        table = queue.pop()
        for ref in by_table[table].payload["references"] if table in by_table else []:
            target = ref["to"]
            if target in have or target not in by_table:
                continue
            have.add(target)
            queue.append(target)
            r = by_table[target]
            found.append(
                RetrievedChunk(id=r.id, type=r.type, title=r.title, content=r.content, payload=r.payload, distance=1.0)
            )
    return found
