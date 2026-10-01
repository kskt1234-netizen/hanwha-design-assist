import hashlib
import math
import re
from typing import Protocol

from app.config import get_settings


class Embedder(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashingEmbedder:
    """문자 2~3-gram 해싱 임베딩. 실제 임베딩 모델(bge-m3 등)을 정하기 전까지 쓰는 임시 구현.

    한국어 단어 일부가 겹치면 유사도가 올라가므로 용어 검색 데모에는 충분하다.
    """

    def __init__(self, dim: int):
        self.dim = dim

    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in re.findall(r"[0-9A-Za-z가-힣_]+", text.lower()):
            padded = f" {token} "
            for n in (2, 3):
                for i in range(len(padded) - n + 1):
                    h = int.from_bytes(hashlib.md5(padded[i : i + n].encode()).digest()[:4], "little")
                    vec[h % self.dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]


def get_embedder() -> Embedder:
    settings = get_settings()
    if settings.embedding_provider == "hashing":
        return HashingEmbedder(settings.embedding_dim)
    raise ValueError(f"지원하지 않는 임베딩 공급자: {settings.embedding_provider}")
