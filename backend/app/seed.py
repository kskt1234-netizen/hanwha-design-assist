"""도메인 지식을 벡터 저장소에 적재한다: python -m app.seed"""
from app.db import SessionLocal, init_db
from app.rag.retriever import seed_knowledge

if __name__ == "__main__":
    init_db()
    with SessionLocal() as session:
        print(f"knowledge_chunk {seed_knowledge(session)}건 적재")
