from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Banking REST Service"
    DEBUG: bool = True
    API_VERSION: str = "v1"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = "sqlite:///./banking.db"
    API_PREFIX: str = "/api"

    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY must be set in environment variables or .env file")


settings = Settings()
