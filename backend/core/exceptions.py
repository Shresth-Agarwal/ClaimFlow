class AppError(Exception):
    """Base class for all application errors."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code

class UserAlreadyExistsError(AppError):
    def __init__(self, email: str):
        super().__init__(f"User with email {email} already exists.", 400)

class InvalidCredentialsError(AppError):
    def __init__(self):
        super().__init__("Invalid email or password.", 401)