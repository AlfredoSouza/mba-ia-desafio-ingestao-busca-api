from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from src.config import get_settings


DOCUMENTS_DDL = """
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    file_hash TEXT NOT NULL UNIQUE,
    storage_path TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'processing', 'ready', 'failed')),
    page_count INTEGER,
    chunk_count INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    settings = get_settings()
    with psycopg.connect(settings.psycopg_url, row_factory=dict_row) as conn:
        yield conn


def initialize_database() -> None:
    with connection() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.execute(DOCUMENTS_DDL)
        conn.commit()

