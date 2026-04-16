from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.api.deps import get_current_user, require_role
from app.services.pdf_service import pdf_service
from app.utils.chunking import chunker
from app.core.logger import setup_logger

router = APIRouter(prefix="/rag", tags=["RAG"])
logger = setup_logger(__name__)

async def process_document_indexing(document_id: UUID, db: Session):
    """
    Background task to extract text and chunk the document.
    (Vector storage addition in Phase 2).
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        logger.error(f"Background indexing failed: Document {document_id} not found.")
        return

    try:
        # 1. Update status
        doc.status = "processing"
        db.commit()

        # 2. Extract Text
        logger.info(f"Extracting text from: {doc.title}")
        text = pdf_service.extract_text(doc.file_path)

        # 3. Chunk Text
        chunks = chunker.chunk_text(text)
        logger.info(f"Generated {len(chunks)} chunks for {doc.title}")

        # [TODO: Phase 2 - Embeddings and Qdrant storage go here]

        # 4. Final status
        doc.status = "ready"
        db.commit()
        logger.info(f"Indexing complete for {doc.title}")

    except Exception as e:
        logger.error(f"Indexing error for {doc.title}: {e}")
        doc.status = "failed"
        db.commit()

from uuid import UUID

@router.post("/index-document/{identifier}", status_code=status.HTTP_202_ACCEPTED)
async def index_document(
    identifier: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("Analyst")),
    db: Session = Depends(get_db)
):
    """
    Trigger the RAG indexing process for a document by its ID (UUID) or Partial Title.
    Requires Analyst or Admin roles.
    """
    # 1. Identity the document (Smart Identifier logic)
    try:
        doc_uuid = UUID(identifier)
        doc = db.query(Document).filter(
            Document.id == doc_uuid,
            Document.owner_id == current_user.id
        ).first()
    except (ValueError, AttributeError):
        # Search by partial title
        doc = db.query(Document).filter(
            Document.title.ilike(f"%{identifier}%"),
            Document.owner_id == current_user.id
        ).order_by(Document.upload_date.desc()).first()

    if not doc:
        raise HTTPException(
            status_code=404, 
            detail=f"Document '{identifier}' not found"
        )

    if doc.status == "processing":
        return {"message": "Document is already being processed", "status": "processing"}

    background_tasks.add_task(process_document_indexing, doc.id, db)
    
    return {
        "message": "Indexing started in the background",
        "document": doc.title,
        "document_id": doc.id,
        "status": "processing"
    }
