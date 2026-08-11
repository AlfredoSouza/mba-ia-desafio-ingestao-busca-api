from src.services.document_service import _is_pdf


def test_accepts_valid_pdf_signature() -> None:
    assert _is_pdf(b"%PDF-1.7\n", "application/pdf")


def test_rejects_non_pdf_content() -> None:
    assert not _is_pdf(b"not a pdf", "application/pdf")

