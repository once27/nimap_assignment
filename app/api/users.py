from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.models.role import Role
from app.api.deps import require_role, get_current_user
from app.schemas.role import RoleResponse

router = APIRouter(prefix="/users", tags=["Users"])

class ChangeRoleRequest(BaseModel):
    username: str
    role_name: str

@router.post("/change-role")
def change_user_role(
    request: ChangeRoleRequest, 
    current_user: User = Depends(require_role("Admin")), 
    db: Session = Depends(get_db)
):
    """
    Promote or change a user's role. Strictly requires Admin Bearer token.
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
def get_my_roles(current_user: User = Depends(get_current_user)):
    """
    Get roles assigned to the current user.
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
