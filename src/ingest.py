import argparse
import asyncio
from pathlib import Path

from fastapi import UploadFile

from src.database import initialize_database
from src.services.document_service import save_upload
from src.services.ingestion_service import ingest_document


async def run(pdf_path: Path) -> None:
    initialize_database()
    with pdf_path.open("rb") as stream:
        upload = UploadFile(filename=pdf_path.name, file=stream, headers={"content-type": "application/pdf"})
        row, created = await save_upload(upload)
    if created or row["status"] != "ready":
        ingest_document(row["id"])
    print(f"Documento {row['id']} processado.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingere um PDF no PostgreSQL/pgVector.")
    parser.add_argument("pdf", nargs="?", default="document.pdf", type=Path)
    args = parser.parse_args()
    asyncio.run(run(args.pdf))

