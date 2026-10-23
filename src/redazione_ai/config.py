from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    database_url: str
    ollama_url: str = "http://localhost:11434"
    embed_model: str = "nomic-embed-text"
    chat_model: str = "qwen2.5:7b"
    llm_api_key: str | None = None

settings = Settings()