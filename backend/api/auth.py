from fastapi import APIRouter
from backend.api.schemas import UserRegisterDto, UserLoginDto, User, LoginResponse
from backend.services.auth_service import AuthService
from backend.database.mock_db import db

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService(db)

@router.post("/register", response_model=User)
def register(dto: UserRegisterDto):
    return auth_service.register(dto)

@router.post("/login", response_model=LoginResponse)
def login(dto: UserLoginDto):
    token = auth_service.login(dto)
    return {"access_token": token, "token_type": "bearer"}