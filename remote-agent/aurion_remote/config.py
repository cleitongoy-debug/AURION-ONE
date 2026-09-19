from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_token: str
    bind_host: str = "127.0.0.1"
    port: int = 8765
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = ""
    context_file: Path = Path("../Biblia_da_Inteligencia_Artificial_AURION_ONE.docx")
    allow_remote_prompts: bool = False
    allow_local_prompts: bool = True
    motion_lock: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AURION_",
        extra="ignore",
    )


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
