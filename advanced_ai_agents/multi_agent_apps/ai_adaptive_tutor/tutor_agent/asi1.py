from langchain_openai import ChatOpenAI
from pydantic import SecretStr
import os

def _load_secret(key: str) -> SecretStr:
    """Load a secret value from environment variables."""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Secret '{key}' not found in environment variables.")
    return SecretStr(value)

ASI1_API_KEY = _load_secret("ASI1_API_KEY")
ASI1_BASE_URL = _load_secret("ASI1_BASE_URL")
ASI1_MODEL =  _load_secret("ASI1_MODEL")

def create_asi1_client() -> ChatOpenAI:
    model = ChatOpenAI(
        temperature=0.1,
        timeout=60,
        api_key=ASI1_API_KEY,
        base_url=ASI1_BASE_URL.get_secret_value(),
        model=ASI1_MODEL.get_secret_value(),
    )
    return model