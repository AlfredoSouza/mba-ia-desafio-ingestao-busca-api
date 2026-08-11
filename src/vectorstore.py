from functools import lru_cache

from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from src.config import get_settings


@lru_cache
def get_embeddings() -> OpenAIEmbeddings:
    settings = get_settings()
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )


@lru_cache
def get_vectorstore() -> PGVector:
    settings = get_settings()
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=settings.collection_name,
        connection=settings.database_url,
        use_jsonb=True,
    )

