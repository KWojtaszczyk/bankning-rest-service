from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Banking REST Service"
    DEBUG: bool = True
    API_VERSION: str = "v1"

    SECRET_KEY: str = "test-secret-key-please-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = "sqlite:///./banking.db"
    API_PREFIX: str = "/api"

    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Only enforce SECRET_KEY in production (when DEBUG=False)
        if not self.DEBUG and self.SECRET_KEY == "test-secret-key-please-change-in-production":
            raise ValueError("SECRET_KEY must be set in production! Please set a strong secret key in your .env file")


settings = Settings()
