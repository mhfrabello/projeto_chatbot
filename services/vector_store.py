# services/vector_store.py
"""
Índice vetorial em memória (FAISS) para busca por similaridade.
"""
import faiss
import numpy as np


def build_index(vectors: list[list[float]]):
    dimension = len(vectors[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(vectors).astype("float32"))
    return index


def search(index, query_vector: list[float], top_k: int = 4):
    distances, indices = index.search(
        np.array([query_vector]).astype("float32"), top_k
    )
    return indices[0]
