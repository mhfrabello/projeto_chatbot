# services/embedding_service.py
"""
Geração de embeddings usando o Azure OpenAI (mesma conta/chave do chat).
"""
from services.azure_client import client
from config.settings import AZURE_EMBEDDING_DEPLOYMENT


def generate_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        model=AZURE_EMBEDDING_DEPLOYMENT,
        input=text,
    )
    return response.data[0].embedding


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Gera embeddings em lote (mais eficiente que chamar um por um).
    A API da Azure aceita uma lista de textos em 'input'.
    """
    response = client.embeddings.create(
        model=AZURE_EMBEDDING_DEPLOYMENT,
        input=texts,
    )
    # A API retorna os itens na mesma ordem em que foram enviados
    return [item.embedding for item in response.data]
