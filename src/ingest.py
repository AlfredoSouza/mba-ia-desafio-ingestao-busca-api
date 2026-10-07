import argparse
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

if __package__:
    from .search import ROOT, get_settings, get_vectorstore
else:
    from search import ROOT, get_settings, get_vectorstore


def ingest_pdf(pdf_path: str | Path | None = None) -> int:
    settings = get_settings()
    path = Path(pdf_path or settings["pdf_path"])
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        raise FileNotFoundError(f"PDF não encontrado: {path}")
    pages = PyPDFLoader(str(path)).load()
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len,
        add_start_index=True,
    ).split_documents(pages)
    if not chunks:
        raise ValueError("O PDF não contém texto extraível. PDFs digitalizados precisam de OCR.")
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = index
        chunk.metadata["source"] = path.name
    # O desafio usa um único PDF: substitui somente a collection configurada.
    vectorstore = get_vectorstore(settings, reset=True)
    vectorstore.add_documents(chunks, ids=[f"pdf-chunk-{index}" for index in range(len(chunks))])
    print(f"PDF: {path.name}")
    print(f"Ingestão concluída: {len(pages)} páginas e {len(chunks)} chunks.")
    return len(chunks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingere o PDF no PostgreSQL com pgVector.")
    parser.add_argument("pdf", nargs="?", help="Opcional: substitui PDF_PATH do .env.")
    args = parser.parse_args()
    try:
        ingest_pdf(args.pdf)
    except Exception as exc:
        parser.exit(1, f"Erro na ingestão: {exc}\n")
