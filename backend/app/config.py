from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "local"
    groq_api_key: str | None = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


settings = Settings()

