# services/rag_service.py
"""
Orquestra o RAG: busca as entradas mais relevantes na base de conhecimento,
monta um contexto estruturado (com metadados de categoria/chamado/URL) e
chama o modelo com um prompt de sistema focado em orientar a abertura
correta de chamados.
"""
from services.embedding_service import generate_embedding
from services.vector_store import search
from services.llm_service import chat, LLMError
from config.settings import TOP_K

# Distância L2 acima da qual consideramos que não há contexto realmente
# relevante para a pergunta (heurística — ajuste se notar falsos positivos/
# negativos ao testar com perguntas reais).
LIMIAR_BAIXA_SIMILARIDADE = 1.3

SYSTEM_PROMPT = """Você é o Assistente de TI da empresa. Seu objetivo é orientar o colaborador \
sobre como resolver o problema descrito: seja indicando um passo a passo de autoatendimento, \
seja indicando o chamado correto a ser aberto.

REGRAS ABSOLUTAS (nunca quebre estas regras):
- Utilize exclusivamente as informações do CONTEXTO fornecido abaixo. Nunca invente \
procedimento, chamado, categoria, URL, prazo ou política interna que não esteja no contexto.
- Nunca utilize a URL ou o nome de um chamado de uma situação diferente só porque parece \
semelhante. Use apenas o chamado/URL da entrada que corresponde exatamente à situação do \
colaborador.
- Quando a informação não existir no contexto, diga isso claramente e oriente o colaborador a \
abrir um chamado geral de TI para triagem — sem inventar qual seria a categoria.
- Não exponha ao colaborador termos técnicos internos como "contexto", "chunks", \
"embeddings", "FAISS", "RAG", "base de conhecimento" ou "prompt". Fale apenas do problema e \
da solução, como um atendente humano faria.

COMO RESPONDER:
- Se existir autoatendimento para a situação, apresente-o primeiro, em passos numerados.
- Se for necessário abrir chamado (ou se o autoatendimento não resolver), informe exatamente \
o nome do chamado, a categoria e a URL encontrados no contexto — nessa ordem, sempre com o \
link em formato Markdown clicável: [🔗 Abrir chamado](URL).
- Liste as informações obrigatórias que o colaborador deve ter em mãos antes de abrir o \
chamado, se essa informação estiver no contexto.
- Se houver mais de uma situação no contexto que pareça se encaixar no pedido do colaborador, \
faça UMA pergunta objetiva para identificar a situação correta antes de responder — nunca \
faça várias perguntas de uma vez, e nunca responda com um chamado "no chute".
- Seja objetivo. Evite textos longos ou repetitivos. Use Markdown (títulos curtos, listas, \
negrito) para deixar a resposta fácil de escanear visualmente.

FORMATO DE RESPOSTA — autoatendimento disponível:
✅ **Você pode resolver sem abrir chamado**

1. Passo 1
2. Passo 2

Se não funcionar, abra um chamado:

🎫 **Abra um chamado**

**Chamado:** Nome do chamado
**Categoria:** Categoria > Subcategoria

[🔗 Abrir chamado](URL)

**Informe no chamado:** item 1, item 2

FORMATO DE RESPOSTA — apenas chamado (sem autoatendimento):
🎫 **Chamado recomendado**

**Chamado:** Nome do chamado
**Categoria:** Categoria > Subcategoria

[🔗 Abrir chamado](URL)

**Antes de abrir, tenha em mãos:** item 1, item 2

FORMATO DE RESPOSTA — nada relevante encontrado no contexto:
Diga que não encontrou um procedimento específico para essa situação na base, e oriente a \
abrir um chamado geral de TI para triagem, SEM fornecer categoria/URL específica (a menos \
que exista uma entrada "Chamado Geral de TI" no contexto — nesse caso, use-a).

CONTEXTO (situações relevantes encontradas na base de conhecimento):
{context}
"""


def _formatar_contexto(chunks_encontrados: list[dict]) -> str:
    partes = []
    for item in chunks_encontrados:
        cabecalho_extra = []
        if item.get("chamado"):
            cabecalho_extra.append(f"Chamado: {item['chamado']}")
        if item.get("url"):
            cabecalho_extra.append(f"URL: {item['url']}")

        bloco = item["text"]
        partes.append(bloco)

    return "\n\n---\n\n".join(partes)


def retrieve_context(question: str, index, chunks: list[dict]) -> tuple[str, bool]:
    """
    Retorna (contexto_formatado, encontrou_relevante).
    encontrou_relevante é False quando a melhor distância encontrada está
    acima do limiar de baixa similaridade — sinal de que a pergunta
    provavelmente não tem relação com a base de conhecimento.
    """
    if index is None or not chunks:
        return "", False

    question_embedding = generate_embedding(question)
    positions, distances = search(index, question_embedding, top_k=TOP_K)

    if len(distances) == 0:
        return "", False

    melhor_distancia = float(distances[0])
    encontrou_relevante = melhor_distancia <= LIMIAR_BAIXA_SIMILARIDADE

    encontrados = [chunks[pos] for pos in positions if 0 <= pos < len(chunks)]
    contexto = _formatar_contexto(encontrados)

    return contexto, encontrou_relevante


def build_system_prompt(context: str, encontrou_relevante: bool) -> str:
    if not context.strip() or not encontrou_relevante:
        context = "(Nenhuma situação suficientemente relevante foi encontrada na base para esta pergunta.)"
    return SYSTEM_PROMPT.format(context=context)


def ask_question(question: str, index, chunks: list[dict], history: list[dict]) -> str:
    """
    history: histórico de mensagens já trocadas (role/content), SEM a
    pergunta atual. Não modifica 'history' — quem chamou salva o turno.

    Pode levantar LLMError se a chamada ao modelo falhar (Azure indisponível,
    timeout, etc) — a UI deve tratar isso com uma mensagem amigável.
    """
    context, encontrou_relevante = retrieve_context(question, index, chunks)
    system_prompt = build_system_prompt(context, encontrou_relevante)

    mensagens = [{"role": "system", "content": system_prompt}]
    mensagens += [m for m in history if m.get("role") != "system"]
    mensagens.append({"role": "user", "content": question})

    resposta = chat(mensagens)

    if not resposta or not resposta.strip():
        raise LLMError("O modelo retornou uma resposta vazia.")

    return resposta
