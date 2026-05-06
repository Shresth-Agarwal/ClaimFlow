import time
import jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from backend.core.config import settings
from backend.api.schemas import User
from backend.database.db import db

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
security = HTTPBearer()

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_jwt(user: User) -> str:
    payload = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "verified": user.verified,
        "exp": time.time() + settings.EXPIRATION_TIME
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.ALGORITHM)

def get_current_user(auth: HTTPAuthorizationCredentials = Security(security)) -> dict:
    try:
        payload = jwt.decode(auth.credentials, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        if time.time() > payload.get("exp", 0):
            raise HTTPException(status_code=401, detail="Token expired")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(required_role: str):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Specific check for agents
        if required_role == "agent":
            agent_in_db = db.get_by_id(current_user["id"])
            if not agent_in_db or not agent_in_db.verified:
                raise HTTPException(status_code=403, detail="Agent identity not verified")
            
        return current_user
    return role_checker
