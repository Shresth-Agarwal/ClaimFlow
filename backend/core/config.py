import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev_super_secret_key")
    EXPIRATION_TIME: int = int(os.getenv("EXPIRATION_TIME", 3600))
    ALGORITHM: str = "HS256"

settings = Settings()