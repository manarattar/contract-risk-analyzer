from typing import Literal
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/contracts.db"
    storage_backend: Literal["local", "azure_blob"] = "local"
    vector_backend: Literal["chroma", "azure_search"] = "chroma"
    llm_provider: Literal["openai", "azure_openai"] = "openai"
    azure_storage_account_url: str = ""
    azure_storage_container: str = "uploads"
    azure_storage_key: str = ""
    azure_search_endpoint: str = ""
    azure_search_index: str = "contract-chunks"
    azure_search_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_chat_deployment: str = ""
    azure_openai_embedding_deployment: str = ""
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_api_key: str = ""
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
        return self.mock_mode or (self.llm_provider == "openai" and not self.openai_api_key.strip())

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
