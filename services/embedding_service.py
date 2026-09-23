# services/embedding_service.py
"""
Geração de embeddings usando o Azure OpenAI (mesma conta/chave do chat).
"""
import openai

from services.azure_client import client
from config.settings import AZURE_EMBEDDING_DEPLOYMENT


class EmbeddingError(Exception):
    """Erro ao gerar embeddings (autenticação, deployment errado, timeout, etc)."""


def _tratar_erro(erro: Exception) -> EmbeddingError:
    if isinstance(erro, openai.AuthenticationError):
        return EmbeddingError(
            "Falha de autenticação com o Azure OpenAI. Verifique a AZURE_OPENAI_KEY no .env."
        )
    if isinstance(erro, openai.NotFoundError):
        return EmbeddingError(
            "Deployment de embedding não encontrado. Verifique se AZURE_EMBEDDING_DEPLOYMENT "
            "no .env corresponde a um deployment de EMBEDDING (não de chat) criado no Azure."
        )
    if isinstance(erro, openai.RateLimitError):
        return EmbeddingError("Limite de requisições do Azure OpenAI atingido.")
    if isinstance(erro, openai.APITimeoutError):
        return EmbeddingError("O Azure OpenAI demorou demais para responder (timeout).")
    if isinstance(erro, openai.APIConnectionError):
        return EmbeddingError(
            "Não foi possível conectar ao Azure OpenAI. Verifique sua internet e o "
            "AZURE_OPENAI_ENDPOINT no .env."
        )
    return EmbeddingError(f"Erro ao gerar embeddings: {erro}")


def generate_embedding(text: str) -> list[float]:
    try:
        response = client.embeddings.create(
            model=AZURE_EMBEDDING_DEPLOYMENT,
            input=text,
        )
    except openai.APIError as erro:
        raise _tratar_erro(erro) from erro
    return response.data[0].embedding


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Gera embeddings em lote. A API do Azure aceita uma lista de textos em
    'input' e retorna os itens na mesma ordem em que foram enviados.
    """
    try:
        response = client.embeddings.create(
            model=AZURE_EMBEDDING_DEPLOYMENT,
            input=texts,
        )
    except openai.APIError as erro:
        raise _tratar_erro(erro) from erro
    return [item.embedding for item in response.data]
