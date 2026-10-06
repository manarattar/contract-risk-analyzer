from openai import OpenAI, AzureOpenAI
from app.config import get_settings


def get_llm_client():
    settings = get_settings()
    if settings.llm_provider == "openai":
        return OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    options = dict(azure_endpoint=settings.azure_openai_endpoint,
                   api_version=settings.azure_openai_api_version)
    if settings.azure_openai_api_key:
        options["api_key"] = settings.azure_openai_api_key
    else:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
        options["azure_ad_token_provider"] = get_bearer_token_provider(
            DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
    return AzureOpenAI(**options)
