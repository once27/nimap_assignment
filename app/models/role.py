import uuid
from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy import Uuid

from app.db.base import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True, nullable=False)
    permissions = Column(JSON, default=list)

class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    role_id = Column(Uuid(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
