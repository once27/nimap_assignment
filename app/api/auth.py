from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.role import Role
from app.schemas.auth import RegisterRequest, LoginRequest, Token
from app.schemas.user import UserResponse
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    db_user_email = db.query(User).filter(User.email == request.email).first()
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    db_user_username = db.query(User).filter(User.username == request.username).first()
    if db_user_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = get_password_hash(request.password)
    new_user = User(
        username=request.username, 
        email=request.email, 
        hashed_password=hashed_password,
        company_name=request.company_name
    )
    
    client_role = db.query(Role).filter(Role.name == "Client").first()
    if client_role:
        new_user.roles = [client_role]
        
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(
        (User.email == request.username_or_email) | (User.username == request.username_or_email)
    ).first()
    if not db_user or not verify_password(request.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
