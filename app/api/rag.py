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

from app.services.embedding_service import embedding_service
from app.services.vector_db_service import vector_db_service

async def process_document_indexing(document_id: UUID, db: Session):
    """
    Background task to extract text, chunk, vectorize, and store in Qdrant.
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

        if chunks:
            # 4. Generate Embeddings (Phase 2)
            logger.info(f"Generating embeddings for {doc.title}")
            embeddings = embedding_service.generate_embeddings(chunks)

            # 5. Store in Qdrant (Phase 2)
            logger.info(f"Storing chunks in Qdrant for {doc.title}")
            metadata = {
                "title": doc.title,
                "owner_id": str(doc.owner_id),
                "file_path": doc.file_path
            }
            success = vector_db_service.upsert_chunks(
                document_id=str(doc.id),
                chunks=chunks,
                embeddings=embeddings,
                metadata=metadata
            )
            
            if not success:
                raise Exception("Failed to store vectors in Qdrant")

        # 6. Final status
        doc.status = "ready"
        db.commit()
        logger.info(f"Indexing complete for {doc.title}")

    except Exception as e:
        logger.error(f"Indexing error for {doc.title}: {e}")
        doc.status = "failed"
        db.commit()

from uuid import UUID

@router.post("/index-document", status_code=status.HTTP_202_ACCEPTED)
async def index_document(
    background_tasks: BackgroundTasks,
    identifier: str = None,
    current_user: User = Depends(require_role("Analyst")),
    db: Session = Depends(get_db)
):
    """
    Unified indexing endpoint:
    1. Provide 'identifier' as a query param to index a specific document (UUID or Title).
    2. Leave 'identifier' empty to automatically index all pending or failed documents.
    """
    target_docs = []

    if identifier:
        # 1. Identity a single document (Smart Identifier logic)
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
            
        target_docs = [doc]
    else:
        # 2. Bulk process all pending/failed documents
        target_docs = db.query(Document).filter(
            Document.owner_id == current_user.id,
            Document.status.in_(["pending", "failed"])
        ).all()

        if not target_docs:
            return {
                "message": "All documents are already indexed or being processed.",
                "count": 0
            }

    # Trigger background tasks for all identified documents
    for doc in target_docs:
        background_tasks.add_task(process_document_indexing, doc.id, db)
    
    return {
        "message": f"Started indexing {len(target_docs)} document(s) in the background.",
        "documents": [doc.title for doc in target_docs],
        "status": "processing"
    }

@router.delete("/remove-document", status_code=status.HTTP_200_OK)
@router.delete("/remove-document/{id}", status_code=status.HTTP_200_OK)
async def remove_document_embeddings(
    id: UUID = None,
    current_user: User = Depends(require_role("Analyst")),
    db: Session = Depends(get_db)
):
    """
    1. If 'id' is provided: Remove vectors for that specific document.
    2. If 'id' is missing: Automatically clean up any orphaned embeddings in Qdrant 
       that belong to documents no longer in your list.
    """
    if id:
        doc = db.query(Document).filter(
            Document.id == id,
            Document.owner_id == current_user.id
        ).first()

        if not doc:
            raise HTTPException(
                status_code=404, 
                detail=f"Document '{id}' not found"
            )

        # Remove from Qdrant
        success = vector_db_service.delete_document_embeddings(str(id))
        if not success:
            raise HTTPException(status_code=500, detail="Failed to remove embeddings from Qdrant")

        # Reset status
        doc.status = "pending"
        db.commit()

        return {
            "message": f"Embeddings for '{doc.title}' removed successfully. Status reset to pending.",
            "document_id": id
        }
    else:
        # Smart Cleanup: Find all valid IDs for this user
        valid_docs = db.query(Document.id).filter(Document.owner_id == current_user.id).all()
        valid_ids = [str(d.id) for d in valid_docs]

        # Call cleanup
        success = vector_db_service.cleanup_orphaned_embeddings(valid_ids, str(current_user.id))
        if not success:
             raise HTTPException(status_code=500, detail="Failed to perform index cleanup")

        return {
            "message": "Index cleanup complete. All orphaned embeddings for your account have been removed.",
            "valid_documents_tracked": len(valid_ids)
        }

from app.schemas.rag import SearchRequest, SearchResponse
from app.services.search_service import search_service

@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Simplified Semantic Search:
    Takes only a 'query' and returns the top relevant text chunks.
    """
    try:
        results = search_service.search(
            query=request.query,
            owner_id=current_user.id
        )
        
        message = None
        if not results:
            message = "No relevant information found in your documents for this query."

        return {
            "query": request.query,
            "results": results,
            "message": message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
