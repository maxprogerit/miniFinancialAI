from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.current_user import set_current_user_id
from app.core.deps import require_user
from app.schemas import DocumentUploadResult
from app.services.documents import SUPPORTED_EXTENSIONS, extract_text, ingest_document

router = APIRouter()


@router.post(
    "/documents",
    response_model=DocumentUploadResult,
    summary="Upload a financial note for RAG",
    description=(
        "Uploads a note (.txt or .pdf), splits it into overlapping chunks, "
        "embeds each chunk, and stores it so search_financial_knowledge can "
        "retrieve it for the current user."
    ),
)
async def upload_document(
    file: UploadFile = File(...),
    user_id: int = Depends(require_user),
) -> DocumentUploadResult:
    set_current_user_id(user_id)

    if not file.filename or not file.filename.lower().endswith(SUPPORTED_EXTENSIONS):
        raise HTTPException(
            status_code=422,
            detail=f"Only {', '.join(SUPPORTED_EXTENSIONS)} files are supported.",
        )

    content = await file.read()
    try:
        text = extract_text(file.filename, content)
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="Could not read this file - is it a valid, unencrypted .txt/.pdf?",
        )

    if not text.strip():
        raise HTTPException(status_code=422, detail="The uploaded file has no extractable text.")

    chunks_stored = ingest_document(source=file.filename, text=text)

    return DocumentUploadResult(source=file.filename, chunks_stored=chunks_stored)
