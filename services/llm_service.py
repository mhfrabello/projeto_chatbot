# services/llm_service.py
"""
Chamada ao modelo de chat (GPT-5) no Azure OpenAI.
"""
from services.azure_client import client
from config.settings import AZURE_CHAT_DEPLOYMENT


def chat(messages: list[dict]) -> str:
    """
    messages: lista no formato [{"role": "system"/"user"/"assistant", "content": "..."}]

    Nota: o GPT-5 (modelo de raciocínio) só aceita o valor padrão de
    'temperature' (1) — por isso o parâmetro não é enviado aqui. Passar
    qualquer outro valor causa erro 400 (unsupported_value) da API.
    """
    response = client.chat.completions.create(
        model=AZURE_CHAT_DEPLOYMENT,
        messages=messages,
    )
    return response.choices[0].message.content