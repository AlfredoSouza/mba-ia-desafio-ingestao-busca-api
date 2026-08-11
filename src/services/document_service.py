import hashlib
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile

from src.config import get_settings
from src.database import connection


class InvalidPdfError(ValueError):
    pass


class UploadTooLargeError(ValueError):
    pass


def _is_pdf(content: bytes, content_type: str | None) -> bool:
    return content.startswith(b"%PDF-") and content_type in {
        "application/pdf",
        "application/octet-stream",
        None,
    }


async def save_upload(upload: UploadFile) -> tuple[dict, bool]:
    settings = get_settings()
    content = await upload.read(settings.max_upload_size_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise UploadTooLargeError(f"O PDF excede {settings.max_upload_size_mb} MB.")
    if not _is_pdf(content, upload.content_type):
        raise InvalidPdfError("O arquivo enviado não é um PDF válido.")

    file_hash = hashlib.sha256(content).hexdigest()
    with connection() as conn:
        existing = conn.execute("SELECT * FROM documents WHERE file_hash = %s", (file_hash,)).fetchone()
        if existing:
            return existing, False

    document_id = uuid4()
    filename = Path(upload.filename or "document.pdf").name
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    storage_path = settings.upload_dir / f"{document_id}.pdf"
    storage_path.write_bytes(content)

    with connection() as conn:
        row = conn.execute(
            """
            INSERT INTO documents (id, filename, content_type, file_hash, storage_path, status)
            VALUES (%s, %s, %s, %s, %s, 'pending')
            RETURNING *
            """,
            (document_id, filename, upload.content_type or "application/pdf", file_hash, str(storage_path)),
        ).fetchone()
        conn.commit()
    return row, True


def get_document(document_id: UUID) -> dict | None:
    with connection() as conn:
        return conn.execute("SELECT * FROM documents WHERE id = %s", (document_id,)).fetchone()


def to_response(row: dict) -> dict:
    return {
        "document_id": row["id"],
        "filename": row["filename"],
        "status": row["status"],
        "page_count": row.get("page_count"),
        "chunk_count": row.get("chunk_count"),
        "error": row.get("error_message"),
        "created_at": row.get("created_at"),
    }

