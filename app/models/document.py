import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Uuid
from sqlalchemy.orm import relationship

from app.db.base import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, index=True, nullable=False)
    company_name = Column(String, index=True, nullable=True) # e.g., Acme Corp
    document_type = Column(String, index=True, nullable=True) # e.g., invoice, report, contract
    file_path = Column(String, nullable=False)
    file_hash = Column(String, index=True, nullable=True)
    status = Column(String, default="uploaded") # uploaded, processing, ready
    tags = Column(JSON, default=list)
    upload_date = Column(DateTime, default=datetime.utcnow)
    
    owner_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="documents")
