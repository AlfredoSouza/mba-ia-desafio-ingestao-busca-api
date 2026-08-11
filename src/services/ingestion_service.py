from uuid import UUID

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.database import connection
from src.services.document_service import get_document
from src.vectorstore import get_vectorstore


def ingest_document(document_id: UUID) -> None:
    row = get_document(document_id)
    if not row or row["status"] == "ready":
        return

    try:
        with connection() as conn:
            conn.execute(
                "UPDATE documents SET status = 'processing', error_message = NULL, updated_at = NOW() WHERE id = %s",
                (document_id,),
            )
            conn.commit()

        pages = PyPDFLoader(row["storage_path"]).load()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            length_function=len,
            add_start_index=True,
        )
        chunks = splitter.split_documents(pages)
        for index, chunk in enumerate(chunks):
            chunk.metadata.update(
                {
                    "document_id": str(document_id),
                    "filename": row["filename"],
                    "chunk_index": index,
                }
            )

        ids = [f"{document_id}:{index}" for index in range(len(chunks))]
        get_vectorstore().add_documents(chunks, ids=ids)

        with connection() as conn:
            conn.execute(
                """
                UPDATE documents
                SET status = 'ready', page_count = %s, chunk_count = %s,
                    error_message = NULL, updated_at = NOW()
                WHERE id = %s
                """,
                (len(pages), len(chunks), document_id),
            )
            conn.commit()
    except Exception as exc:
        with connection() as conn:
            conn.execute(
                """
                UPDATE documents
                SET status = 'failed', error_message = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (str(exc)[:2000], document_id),
            )
            conn.commit()
        raise

