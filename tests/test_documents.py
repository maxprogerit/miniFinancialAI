"""Document upload tests: text extraction (.txt and real .pdf bytes, not
mocked) plus the API-level happy/error paths (ingest_document mocked there
- embeddings/DB writes are covered by the RAG tests elsewhere)."""
import app.api.documents as documents_api
from app.services.documents import extract_text


def _minimal_pdf(text: str) -> bytes:
    """Hand-built single-page PDF with one text-showing content stream -
    good enough for pypdf to extract `text` back out, without pulling in
    a PDF-generation library just for test fixtures."""
    content_stream = f"BT /F1 12 Tf 10 50 Td ({text}) Tj ET".encode()
    objects = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/MediaBox[0 0 200 100]/Contents 5 0 R>>",
        b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
        b"<</Length " + str(len(content_stream)).encode() + b">>\nstream\n" + content_stream + b"\nendstream",
    ]

    pdf = b"%PDF-1.4\n"
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{i} 0 obj".encode() + obj + b"\nendobj\n"

    xref_offset = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n".encode()
    pdf += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        pdf += f"{off:010d} 00000 n \n".encode()
    pdf += f"trailer\n<</Size {len(objects) + 1}/Root 1 0 R>>\nstartxref\n{xref_offset}\n%%EOF".encode()
    return pdf


def test_extract_text_txt():
    assert extract_text("note.txt", b"hello world") == "hello world"


def test_extract_text_pdf_real_bytes():
    pdf_bytes = _minimal_pdf("Hello Financial World")
    assert extract_text("note.pdf", pdf_bytes) == "Hello Financial World"


def test_extract_text_corrupted_pdf_raises():
    import pytest

    with pytest.raises(Exception):
        extract_text("note.pdf", b"this is not a real pdf")


def test_documents_upload_accepts_txt(client, demo1_token, monkeypatch):
    monkeypatch.setattr(documents_api, "ingest_document", lambda source, text: 2)

    resp = client.post(
        "/documents",
        files={"file": ("notes.txt", b"some note content", "text/plain")},
        headers={"Authorization": f"Bearer {demo1_token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"source": "notes.txt", "chunks_stored": 2}


def test_documents_upload_accepts_real_pdf(client, demo1_token, monkeypatch):
    captured = {}
    monkeypatch.setattr(
        documents_api, "ingest_document",
        lambda source, text: captured.update(source=source, text=text) or 1,
    )

    pdf_bytes = _minimal_pdf("Saving for a trip")
    resp = client.post(
        "/documents",
        files={"file": ("trip.pdf", pdf_bytes, "application/pdf")},
        headers={"Authorization": f"Bearer {demo1_token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"source": "trip.pdf", "chunks_stored": 1}
    assert captured["text"] == "Saving for a trip"


def test_documents_upload_rejects_unsupported_extension(client, demo1_token):
    resp = client.post(
        "/documents",
        files={"file": ("notes.docx", b"whatever", "application/octet-stream")},
        headers={"Authorization": f"Bearer {demo1_token}"},
    )
    assert resp.status_code == 422


def test_documents_upload_rejects_corrupted_pdf(client, demo1_token):
    resp = client.post(
        "/documents",
        files={"file": ("broken.pdf", b"not a real pdf", "application/pdf")},
        headers={"Authorization": f"Bearer {demo1_token}"},
    )
    assert resp.status_code == 422
