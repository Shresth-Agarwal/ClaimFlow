from typing import Optional, List
from backend.database.interfaces import IUserRepository
from backend.api.schemas import User

class MockUserRepository(IUserRepository):
    """
    In-memory database implementation.
    """
    def __init__(self):
        self.users: List[User] = []

    def create_user(self, user: User) -> User:
        self.users.append(user)
        return user

    def get_by_email(self, email: str) -> Optional[User]:
        for u in self.users:
            if u.email == email:
                return u
        return None
        
    def get_by_id(self, user_id: int) -> Optional[User]:
        for u in self.users:
            if u.id == user_id:
                return u
        return None

    def update_verification_status(self, user_id: int, status: bool) -> bool:
        user = self.get_by_id(user_id)
        if user:
            user.verified = status
            return True
        return False

# Singleton instance to be imported by services
db = MockUserRepository()