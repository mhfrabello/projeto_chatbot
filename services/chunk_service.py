# services/chunk_service.py
"""
Transforma cada KnowledgeEntry em um chunk pronto para indexação.

Diferente de um chunker por tamanho fixo (que pode cortar uma URL ou um
campo no meio), aqui cada entrada estruturada vira exatamente UM chunk,
preservando todos os seus metadados (categoria, chamado, URL, palavras-chave).
Isso é o que garante que o link do chamado nunca se perde.

Para entradas de fallback (texto livre, sem "### ENTRADA:"), aplicamos uma
quebra por tamanho apenas se o texto for muito grande — a maioria dos casos
reais vem da base estruturada e não passa por aqui.
"""
from services.document_service import KnowledgeEntry

TAMANHO_MAXIMO_FALLBACK = 1200  # chars — só afeta entradas de fallback (texto livre)


def build_chunks(entradas: list[KnowledgeEntry]) -> list[dict]:
    """
    Retorna uma lista de dicts prontos para embedding + indexação:
    {"text": ..., "source": ..., "titulo": ..., "categoria": ...,
     "chamado": ..., "url": ..., "palavras_chave": ...}
    """
    chunks = []

    for entrada in entradas:
        texto = entrada.texto_completo

        if len(texto) <= TAMANHO_MAXIMO_FALLBACK or entrada.chamado or entrada.url:
            # Entrada estruturada (tem chamado/URL) ou texto curto: um chunk único.
            chunks.append(_entry_to_chunk(entrada, texto))
        else:
            # Fallback para texto livre muito longo: divide preservando o título
            # em cada pedaço, para não perder o contexto de qual entrada é.
            for pedaco in _split_by_size(texto, TAMANHO_MAXIMO_FALLBACK):
                chunks.append(_entry_to_chunk(entrada, pedaco))

    return chunks


def _entry_to_chunk(entrada: KnowledgeEntry, texto: str) -> dict:
    return {
        "text": texto,
        "source": entrada.source,
        "titulo": entrada.titulo,
        "categoria": entrada.categoria_secao,
        "chamado": entrada.chamado,
        "url": entrada.url,
        "palavras_chave": entrada.palavras_chave,
    }


def _split_by_size(text: str, chunk_size: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    return [text[i:i + chunk_size].strip() for i in range(0, len(text), chunk_size)]
