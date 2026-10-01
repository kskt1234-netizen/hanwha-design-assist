from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    database_url: str = "postgresql+psycopg://design:design@localhost:5432/design"

    # LLM 공급자는 아직 미정. "mock"은 규칙 기반 임시 구현으로, 키 없이 전체 흐름을 돌려볼 수 있다.
    llm_provider: str = "mock"
    llm_model: str = ""
    llm_api_key: str = ""

    # 임베딩 모델도 미정. "hashing"은 문자 n-gram 해싱 임시 구현.
    embedding_provider: str = "hashing"
    embedding_dim: int = 256

    rag_top_k: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
