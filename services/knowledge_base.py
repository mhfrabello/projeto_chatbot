# services/knowledge_base.py
"""
Monta a base de conhecimento completa: lê base_conhecimento.md (e outros
arquivos em knowledge/), gera os chunks com metadados, cria os embeddings
e constrói o índice FAISS.
"""
from services.document_service import load_knowledge_entries
from services.chunk_service import build_chunks
from services.embedding_service import generate_embeddings_batch, EmbeddingError
from services.vector_store import build_index
from config.settings import KNOWLEDGE_DIR


class KnowledgeBaseError(Exception):
    """Erro ao montar a base de conhecimento (arquivo inválido, Azure indisponível, etc)."""


def build_knowledge_base():
    """
    Retorna (index, chunks, num_entradas).
    Se não houver conteúdo válido, retorna (None, [], 0) sem lançar erro
    — quem chama decide como avisar o usuário.
    Lança KnowledgeBaseError se a geração de embeddings falhar (ex: Azure
    fora do ar, deployment errado, etc) — isso SIM precisa ser tratado
    explicitamente pela UI, pois indica um problema de configuração.
    """
    entradas = load_knowledge_entries(KNOWLEDGE_DIR)

    if not entradas:
        return None, [], 0

    chunks = build_chunks(entradas)

    if not chunks:
        return None, [], len(entradas)

    textos = [c["text"] for c in chunks]

    try:
        vectors = generate_embeddings_batch(textos)
    except EmbeddingError as erro:
        raise KnowledgeBaseError(str(erro)) from erro
    except Exception as erro:
        raise KnowledgeBaseError(
            f"Falha ao gerar embeddings da base de conhecimento: {erro}"
        ) from erro

    index = build_index(vectors)

    return index, chunks, len(entradas)
