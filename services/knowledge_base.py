# services/knowledge_base.py
"""
Monta a base de conhecimento completa: lê os arquivos da pasta knowledge/,
quebra em chunks, gera embeddings e constrói o índice FAISS.
"""
from services.document_service import load_documents
from services.chunk_service import create_chunks_from_documents
from services.embedding_service import generate_embeddings_batch
from services.vector_store import build_index
from config.settings import KNOWLEDGE_DIR, CHUNK_SIZE, CHUNK_OVERLAP


def build_knowledge_base():
    """
    Retorna (index, chunks, num_documentos).
    Se não houver documentos válidos, retorna (None, [], 0).
    """
    documentos = load_documents(KNOWLEDGE_DIR)

    if not documentos:
        return None, [], 0

    chunks = create_chunks_from_documents(documentos, CHUNK_SIZE, CHUNK_OVERLAP)

    if not chunks:
        return None, [], len(documentos)

    textos = [c["text"] for c in chunks]
    vectors = generate_embeddings_batch(textos)
    index = build_index(vectors)

    return index, chunks, len(documentos)
