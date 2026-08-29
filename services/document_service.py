# services/document_service.py
"""
Carrega todos os documentos da pasta de conhecimento (knowledge/).
Suporta .md, .txt e .pdf.
"""
import os
from pypdf import PdfReader


def _read_pdf(path: str) -> str:
    reader = PdfReader(path)
    conteudo = []
    for page in reader.pages:
        texto = page.extract_text() or ""
        conteudo.append(texto)
    return "\n".join(conteudo)


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_documents(knowledge_dir: str) -> list[dict]:
    """
    Retorna uma lista de {"source": nome_do_arquivo, "text": conteúdo}
    para cada arquivo suportado dentro da pasta (não entra em subpastas).
    """
    documentos = []

    if not os.path.isdir(knowledge_dir):
        return documentos

    for nome_arquivo in sorted(os.listdir(knowledge_dir)):
        caminho = os.path.join(knowledge_dir, nome_arquivo)

        if not os.path.isfile(caminho):
            continue

        extensao = nome_arquivo.lower().rsplit(".", 1)[-1] if "." in nome_arquivo else ""

        try:
            if extensao == "pdf":
                texto = _read_pdf(caminho)
            elif extensao in ("md", "txt"):
                texto = _read_text(caminho)
            else:
                continue  # ignora arquivos de tipos não suportados

            if texto.strip():
                documentos.append({"source": nome_arquivo, "text": texto})

        except Exception as erro:
            # Não derruba o app inteiro por causa de um arquivo problemático
            print(f"[document_service] Erro ao ler '{nome_arquivo}': {erro}")

    return documentos
