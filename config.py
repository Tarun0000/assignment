from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL = "postgresql://user:password@localhost:5432/image_processor"
    UPLOAD_DIR = "processed_images"

settings = Settings()