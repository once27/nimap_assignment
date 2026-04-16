from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.models.role import Role
from app.api.deps import require_role

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
