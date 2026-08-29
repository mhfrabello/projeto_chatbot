# services/azure_client.py
"""
Cliente único do Azure OpenAI, compartilhado pelo chat e pelos embeddings.
Autenticação simples via API Key (AZURE_OPENAI_KEY).
"""
from openai import AzureOpenAI

from config.settings import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_API_VERSION,
)

client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
)
