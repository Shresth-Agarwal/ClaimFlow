from abc import ABC, abstractmethod
from typing import Optional
from backend.api.schemas import User

class IUserRepository(ABC):
    """
    Abstract interface for User data access.
    Any database implementation (Mock, SQL, DynamoDB) must implement these methods.
    """
    
    @abstractmethod
    def create_user(self, user: User) -> User:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    def update_verification_status(self, user_id: int, status: bool) -> bool:
        pass