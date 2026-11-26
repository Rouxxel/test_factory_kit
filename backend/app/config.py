from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    GEMINI_API_KEY: str = ""
    MODEL_NAME: str = "gemini-2.5-flash"
    PORT: int = 8000


settings = Settings()
