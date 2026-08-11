from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    document_id: UUID
    filename: str
    status: Literal["pending", "processing", "ready", "failed"]
    page_count: int | None = None
    chunk_count: int | None = None
    error: str | None = None
    created_at: datetime | None = None


class QuestionRequest(BaseModel):
    document_id: UUID
    question: str = Field(min_length=1, max_length=4000)


class SourceChunk(BaseModel):
    page: int | None = None
    chunk_index: int | None = None
    score: float
    content: str


class AnswerResponse(BaseModel):
    document_id: UUID
    answer: str
    sources: list[SourceChunk]

