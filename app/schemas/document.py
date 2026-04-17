from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import List, Optional

class DocumentBase(BaseModel):
    title: str

class DocumentCreate(BaseModel):
    pass

class DocumentUpdate(BaseModel):
    title: Optional[str] = None

class DocumentResponse(DocumentBase):
    id: UUID
    company_name: Optional[str] = None
    document_type: Optional[str] = None
    file_path: str
    file_hash: Optional[str] = None
    status: str
    upload_date: datetime
    owner_id: UUID

    model_config = ConfigDict(from_attributes=True)
