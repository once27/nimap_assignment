from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.models.role import Role
from app.api.deps import require_role, get_current_user
from app.schemas.role import RoleResponse

router = APIRouter(prefix="/users", tags=["Users & Roles"])

class AssignRoleRequest(BaseModel):
    username: str
    role_name: str

@router.post("/assign-role")
def assign_user_role(
    request: AssignRoleRequest, 
    current_user: User = Depends(require_role("Admin")), 
    db: Session = Depends(get_db)
):
    """
    Assign a role to a user. Strictly requires Admin Bearer token.
    """
    target_user = db.query(User).filter(User.username == request.username).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    new_role = db.query(Role).filter(Role.name == request.role_name).first()
    if not new_role:
        raise HTTPException(status_code=404, detail="Role not found")
        
    target_user.roles = [new_role]
    db.commit()
    return {"status": "success", "message": f"User {request.username} is now {request.role_name}"}

@router.get("/me/roles", response_model=List[RoleResponse])
def get_my_role(current_user: User = Depends(get_current_user)):
    """
    Get role assigned to the current user.
    """
    return current_user.roles

@router.get("/me/permissions", response_model=List[str])
def get_my_permissions(current_user: User = Depends(get_current_user)):
    """
    Get all unique permissions assigned to the current user.
    """
    permissions = set()
    for role in current_user.roles:
        for perm in role.permissions:
            permissions.add(perm)
    return list(permissions)

@router.get("/roles", response_model=List[RoleResponse])
def list_roles(
    current_user=Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """
    Get all system roles. Requires Admin permissions.
    """
    return db.query(Role).all()
