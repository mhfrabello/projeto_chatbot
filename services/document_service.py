# services/document_service.py
"""
Lê e interpreta a base de conhecimento (knowledge/base_conhecimento.md).

O arquivo é dividido em blocos "### ENTRADA: ..." — cada bloco é uma unidade
atômica de atendimento (um problema/situação completo, com seus próprios
metadados: categoria, palavras-chave, chamado, URL, etc). Isso é o que
garante que a URL e os dados do chamado NUNCA se percam durante o chunking:
cada entrada vira exatamente um chunk, nunca é cortada no meio.

Também aceita arquivos .md/.txt soltos na pasta knowledge/ como fallback
(tratados como texto livre, sem os metadados estruturados) — assim, se o
usuário adicionar um arquivo extra sem seguir o formato, o app ainda
funciona, só que sem os campos extras de metadado.
"""
import os
import re
from dataclasses import dataclass


@dataclass
class KnowledgeEntry:
    """Uma entrada de conhecimento (um problema/situação completo)."""
    titulo: str
    texto_completo: str          # texto integral da entrada, enviado ao modelo
    categoria_secao: str = ""    # a seção "## CATEGORIA: ..." em que está
    chamado: str = ""
    url: str = ""
    palavras_chave: str = ""
    source: str = "base_conhecimento.md"


def _parse_base_estruturada(texto: str, nome_arquivo: str) -> list[KnowledgeEntry]:
    entradas: list[KnowledgeEntry] = []

    # Quebra o arquivo em seções "## CATEGORIA: X"
    secoes = re.split(r"(?m)^##\s+CATEGORIA:\s*(.+)$", texto)
    # secoes[0] é o cabeçalho antes da primeira categoria (ignorado)
    # a partir daí, alterna: nome_categoria, conteudo_categoria, nome_categoria, conteudo...

    for i in range(1, len(secoes), 2):
        nome_categoria = secoes[i].strip()
        conteudo_categoria = secoes[i + 1] if i + 1 < len(secoes) else ""

        # Dentro de cada categoria, quebra em blocos "### ENTRADA: X"
        blocos = re.split(r"(?m)^###\s+ENTRADA:\s*(.+)$", conteudo_categoria)

        for j in range(1, len(blocos), 2):
            titulo = blocos[j].strip()
            corpo = blocos[j + 1] if j + 1 < len(blocos) else ""
            corpo = corpo.split("\n---", 1)[0].strip()  # corta no separador de fim de bloco

            if not corpo:
                continue

            chamado = _extrair_campo(corpo, "Chamado")
            url = _extrair_campo(corpo, "URL")
            palavras_chave = _extrair_campo(corpo, "Palavras-chave")

            texto_completo = (
                f"Categoria: {nome_categoria}\n"
                f"Situação: {titulo}\n\n"
                f"{corpo}"
            )

            entradas.append(
                KnowledgeEntry(
                    titulo=titulo,
                    texto_completo=texto_completo,
                    categoria_secao=nome_categoria,
                    chamado=chamado,
                    url=url,
                    palavras_chave=palavras_chave,
                    source=nome_arquivo,
                )
            )

    return entradas


def _extrair_campo(corpo: str, nome_campo: str) -> str:
    match = re.search(rf"(?m)^{re.escape(nome_campo)}:\s*(.+)$", corpo)
    return match.group(1).strip() if match else ""


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_knowledge_entries(knowledge_dir: str) -> list[KnowledgeEntry]:
    """
    Retorna todas as entradas de conhecimento encontradas na pasta.

    - base_conhecimento.md (ou qualquer .md com blocos "### ENTRADA:") é
      interpretado de forma estruturada, uma entrada = um chunk.
    - Outros .md/.txt sem esse formato são tratados como um único bloco de
      texto livre (fallback, sem metadados de chamado/URL).
    """
    entradas: list[KnowledgeEntry] = []

    if not os.path.isdir(knowledge_dir):
        return entradas

    for nome_arquivo in sorted(os.listdir(knowledge_dir)):
        caminho = os.path.join(knowledge_dir, nome_arquivo)

        if not os.path.isfile(caminho):
            continue

        extensao = nome_arquivo.lower().rsplit(".", 1)[-1] if "." in nome_arquivo else ""
        if extensao not in ("md", "txt"):
            continue

        try:
            texto = _read_text(caminho)
        except Exception as erro:
            print(f"[document_service] Erro ao ler '{nome_arquivo}': {erro}")
            continue

        if not texto.strip():
            continue

        if "### ENTRADA:" in texto:
            entradas.extend(_parse_base_estruturada(texto, nome_arquivo))
        else:
            # Fallback: arquivo solto sem o formato estruturado.
            entradas.append(
                KnowledgeEntry(
                    titulo=nome_arquivo,
                    texto_completo=texto.strip(),
                    source=nome_arquivo,
                )
            )

    return entradas
