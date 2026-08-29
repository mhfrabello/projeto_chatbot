# services/llm_service.py
"""
Chamada ao modelo de chat (GPT-5) no Azure OpenAI.
"""
from services.azure_client import client
from config.settings import AZURE_CHAT_DEPLOYMENT, AZURE_CHAT_TEMPERATURE


def chat(messages: list[dict]) -> str:
    """
    messages: lista no formato [{"role": "system"/"user"/"assistant", "content": "..."}]
    """
    response = client.chat.completions.create(
        model=AZURE_CHAT_DEPLOYMENT,
        messages=messages,
        temperature=AZURE_CHAT_TEMPERATURE,
    )
    return response.choices[0].message.content
