from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    username: str = Field(..., pattern="^[a-zA-Z0-9]+$", description="Alphanumeric only")
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    username_or_email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
