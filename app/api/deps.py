import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.core.logger import setup_logger

security = HTTPBearer()
logger = setup_logger(__name__)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            logger.warning("Token provided but missing 'sub' identifier payload.")
            raise credentials_exception
            
        try:
            parsed_id = uuid.UUID(user_id_str)
        except ValueError as e:
            logger.error(f"Malformed UUID in token payload: '{user_id_str}' | Error: {e}")
            raise credentials_exception
            
    except JWTError as e:
        logger.error(f"JWTDecode validation failed: {e}")
        raise credentials_exception
        
    user = db.query(User).filter(User.id == parsed_id).first()
    if user is None:
        logger.warning(f"Valid token successfully decoded, but user ID {parsed_id} no longer exists in DB.")
        raise credentials_exception
    return user

def require_role(required_role: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        # Allow Admin to bypass all permission checks
        is_authorized = any(role.name in ["Admin", required_role] for role in current_user.roles)
        if not is_authorized:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return current_user
    return role_checker
