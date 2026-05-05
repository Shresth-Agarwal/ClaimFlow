from fastapi import HTTPException
from backend.api.schemas import UserRegisterDto, UserLoginDto, User
from backend.database.interfaces import IUserRepository
from backend.core.security import get_password_hash, verify_password, create_jwt

class AuthService:
    def __init__(self, db: IUserRepository):
        self.db = db
        self.counter = 1  # Simple ID generator for the mock database

    def register(self, dto: UserRegisterDto) -> User:
        if dto.role not in {"user", "agent"}:
            raise HTTPException(status_code=400, detail="Role must be either 'user' or 'agent'")

        if self.db.get_by_email(dto.email):
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        new_user = User(
            id=self.counter,
            username=dto.username,
            email=dto.email,
            role=dto.role,
            password=get_password_hash(dto.password),
            verified=False
        )
        
        created_user = self.db.create_user(new_user)
        self.counter += 1
        return created_user

    def login(self, dto: UserLoginDto) -> str:
        user = self.db.get_by_email(dto.email)
        if not user or not verify_password(dto.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        return create_jwt(user)