from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://root:password@localhost:3306/flashlang"
    jwt_access_secret: str = "dev_access_secret_min_32_chars_long"
    jwt_refresh_secret: str = "dev_refresh_secret_min_32_chars_long"
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7
    bcrypt_rounds: int = 12
    frontend_url: str = "http://localhost:5173"

    model_config = {"env_file": ".env"}


settings = Settings()
