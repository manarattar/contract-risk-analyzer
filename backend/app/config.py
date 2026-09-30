from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4o-mini"
    # Jev (TypeSafe) decides each clause's category when a key is set; the LLM
    # then only writes the explanations. Empty key = the LLM decides, as before.
    typesafe_api_key: str = ""
    jev_model: str = "jev-latest"
    mock_mode: bool = False
    cors_origins: str = "*"  # comma-separated URLs, or "*" for all

    @property
    def use_mock(self) -> bool:
        return self.mock_mode or not self.openai_api_key.strip()

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "protected_namespaces": ("settings_",),
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
