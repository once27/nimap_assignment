from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleResponse
from app.api.deps import require_role

router = APIRouter(prefix="/roles", tags=["Roles"])

@router.get("/", response_model=List[RoleResponse])
def list_roles(
    current_user=Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """
    Get all roles. Requires Admin permissions.
    """
    return db.query(Role).all()

@router.get("/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: UUID,
    current_user=Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """
    Get a specific role by ID. Requires Admin permissions.
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role
