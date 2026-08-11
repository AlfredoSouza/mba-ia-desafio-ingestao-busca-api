from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def test_required_chunk_configuration() -> None:
    text = "A" * 2200
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents([Document(page_content=text)])

    assert len(chunks) >= 3
    assert all(len(chunk.page_content) <= 1000 for chunk in chunks)

