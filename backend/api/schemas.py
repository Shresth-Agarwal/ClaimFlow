from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str # 'user' or 'agent'
    password: str # Hashed
    verified: bool = False

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    verified: bool = False

class UserRegisterDto(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str

class IDProofDto(BaseModel):
    id_type: str
    id_number: str
    metadata: Optional[dict] = None

class VerificationResponse(BaseModel):
    status: str
    message: str
    verification_source: str = "id_proof"

class UserLoginDto(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"