from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "2Care Voice AI Agent"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    redis_url: str = "redis://localhost:6379/0"
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_tts_model: str = "tts-1"
    openai_whisper_model: str = "whisper-1"
    default_language: str = "en"
    session_ttl_seconds: int = 1800

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()