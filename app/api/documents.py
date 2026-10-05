from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas import DocumentUploadResult
from app.services.documents import ingest_document

router = APIRouter()


@router.post(
    "/documents",
    response_model=DocumentUploadResult,
    summary="Upload a financial note for RAG",
    description=(
        "Uploads a plain-text note, splits it into overlapping chunks, "
        "embeds each chunk, and stores it so search_financial_knowledge can "
        "retrieve it for the current user. Only .txt files are supported "
        "right now - PDF support is not implemented yet."
    ),
)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResult:
    if not file.filename or not file.filename.lower().endswith(".txt"):
        raise HTTPException(
            status_code=422,
            detail="Only .txt files are supported right now.",
        )

    content = await file.read()
    text = content.decode("utf-8")

    if not text.strip():
        raise HTTPException(status_code=422, detail="The uploaded file is empty.")

    chunks_stored = ingest_document(source=file.filename, text=text)

    return DocumentUploadResult(source=file.filename, chunks_stored=chunks_stored)
