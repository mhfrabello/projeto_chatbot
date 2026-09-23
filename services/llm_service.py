# services/llm_service.py
"""
Chamada ao modelo de chat (GPT-5) no Azure OpenAI.
"""
import openai

from services.azure_client import client
from config.settings import AZURE_CHAT_DEPLOYMENT


class LLMError(Exception):
    """Erro ao chamar o modelo de chat (autenticação, timeout, indisponibilidade, etc)."""


def chat(messages: list[dict]) -> str:
    """
    messages: lista no formato [{"role": "system"/"user"/"assistant", "content": "..."}]

    Nota: o GPT-5 (modelo de raciocínio) só aceita o valor padrão de
    'temperature' (1) — por isso o parâmetro não é enviado aqui. Passar
    qualquer outro valor causa erro 400 (unsupported_value) da API.
    """
    try:
        response = client.chat.completions.create(
            model=AZURE_CHAT_DEPLOYMENT,
            messages=messages,
        )
    except openai.AuthenticationError as erro:
        raise LLMError(
            "Falha de autenticação com o Azure OpenAI. Verifique a AZURE_OPENAI_KEY no .env."
        ) from erro
    except openai.NotFoundError as erro:
        raise LLMError(
            "Deployment do modelo de chat não encontrado. Verifique AZURE_CHAT_DEPLOYMENT "
            "e AZURE_OPENAI_ENDPOINT no .env."
        ) from erro
    except openai.RateLimitError as erro:
        raise LLMError(
            "Limite de requisições do Azure OpenAI atingido. Tente novamente em instantes."
        ) from erro
    except openai.APITimeoutError as erro:
        raise LLMError("O Azure OpenAI demorou demais para responder (timeout).") from erro
    except openai.APIConnectionError as erro:
        raise LLMError(
            "Não foi possível conectar ao Azure OpenAI. Verifique sua internet e o "
            "AZURE_OPENAI_ENDPOINT no .env."
        ) from erro
    except openai.APIError as erro:
        raise LLMError(f"Erro ao chamar o Azure OpenAI: {erro}") from erro

    return response.choices[0].message.content
