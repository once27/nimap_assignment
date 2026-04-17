import os
import uuid
from uuid import UUID
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.api.deps import get_current_user
from app.core.logger import setup_logger

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = setup_logger(__name__)

UPLOAD_DIR = "uploads"

import hashlib

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document. Minimal interface: only accepts the file.
    Implements SHA256 deduplication.
    """
    # Create upload directory if it doesn't exist
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    # Read file content for hashing
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Check for duplicates
    existing_doc = db.query(Document).filter(Document.file_hash == file_hash).first()
    if existing_doc:
        logger.info(f"Duplicate document detected (hash: {file_hash}). Returning existing record.")
        return existing_doc

    # Generate a unique filename to prevent disk collisions
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save file"
        )
    finally:
        await file.close()

    # Create DB record
    db_document = Document(
        title=file.filename,  # Use filename as title
        file_path=file_path,
        file_hash=file_hash,
        status="pending",
        owner_id=current_user.id
    )
    
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    logger.info(f"Document '{file.filename}' uploaded successfully (New, ID: {db_document.id})")
    
    return db_document

@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all documents owned by the current user.
    """
    return db.query(Document).filter(Document.owner_id == current_user.id).all()

@router.get("/{identifier}", response_model=DocumentResponse)
def get_document(
    identifier: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve metadata for a specific document by its ID (UUID) or Partial Title.
    If multiple match, returns the most recent one.
    """
    # 1. Try to parse as UUID
    try:
        doc_uuid = UUID(identifier)
        return db.query(Document).filter(
            Document.id == doc_uuid, 
            Document.owner_id == current_user.id
        ).first() or HTTPException(status_code=404, detail="Document not found")
    except (ValueError, AttributeError):
        # 2. If not a UUID, search by partial title (case-insensitive)
        doc = db.query(Document).filter(
            Document.title.ilike(f"%{identifier}%"), 
            Document.owner_id == current_user.id
        ).order_by(Document.upload_date.desc()).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{identifier}' not found")
    return doc

@router.delete("/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    identifier: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a document by its ID (UUID) or Partial Title.
    If multiple match, deletes the most recent one.
    """
    # 1. Try to parse as UUID
    try:
        doc_uuid = UUID(identifier)
        doc = db.query(Document).filter(
            Document.id == doc_uuid, 
            Document.owner_id == current_user.id
        ).first()
    except (ValueError, AttributeError):
        # 2. If not a UUID, search by partial title (case-insensitive)
        doc = db.query(Document).filter(
            Document.title.ilike(f"%{identifier}%"), 
            Document.owner_id == current_user.id
        ).order_by(Document.upload_date.desc()).first()
    
    if not doc:
        raise HTTPException(
            status_code=404, 
            detail=f"Document '{identifier}' not found"
        )
        
    # Delete from Disk
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
            logger.info(f"File removed from disk: {doc.file_path}")
        except Exception as e:
            logger.error(f"Failed to delete file from disk: {e}")

    # Delete from DB
    db.delete(doc)
    db.commit()
    
    logger.info(f"Document '{identifier}' (matched: {doc.title}) deleted by {current_user.username}")
    return None
