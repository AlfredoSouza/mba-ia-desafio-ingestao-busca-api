from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile, status

from src.database import initialize_database
from src.schemas import AnswerResponse, DocumentResponse, QuestionRequest
from src.services.document_service import (
    InvalidPdfError,
    UploadTooLargeError,
    get_document,
    save_upload,
    to_response,
)
from src.services.ingestion_service import ingest_document
from src.services.question_service import answer_question


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Ingestão e Busca Semântica de PDFs",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> dict:
    try:
        row, created = await save_upload(file)
    except (InvalidPdfError, UploadTooLargeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if created:
        background_tasks.add_task(ingest_document, row["id"])
    return to_response(row)


@app.get("/documents/{document_id}", response_model=DocumentResponse)
def document_status(document_id: UUID) -> dict:
    row = get_document(document_id)
    if not row:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    return to_response(row)


@app.post("/questions", response_model=AnswerResponse)
def ask_question(request: QuestionRequest) -> dict:
    try:
        return answer_question(request.document_id, request.question)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

