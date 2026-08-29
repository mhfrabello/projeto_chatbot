# services/chunk_service.py
"""
Quebra o texto de cada documento em pedaços menores (chunks) para indexação.
Usa uma janela deslizante com overlap para não perder contexto nas bordas.
"""


def create_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []

    if overlap >= chunk_size:
        overlap = 0  # evita loop infinito se configurado errado

    chunks = []
    start = 0
    tamanho_total = len(text)

    while start < tamanho_total:
        end = start + chunk_size
        pedaco = text[start:end].strip()
        if pedaco:
            chunks.append(pedaco)
        start += chunk_size - overlap

    return chunks


def create_chunks_from_documents(
    documentos: list[dict], chunk_size: int, overlap: int
) -> list[dict]:
    """
    documentos: lista de {"source": ..., "text": ...}
    Retorna uma lista de {"source": ..., "text": chunk} — um item por chunk,
    mantendo o nome do arquivo de origem (útil pra citar a fonte na resposta).
    """
    todos_chunks = []
    for doc in documentos:
        pedacos = create_chunks(doc["text"], chunk_size, overlap)
        for pedaco in pedacos:
            todos_chunks.append({"source": doc["source"], "text": pedaco})
    return todos_chunks
