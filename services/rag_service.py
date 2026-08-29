# services/rag_service.py
"""
Orquestra o RAG: busca o contexto relevante na base de conhecimento
e monta a pergunta para o modelo, com um prompt de sistema focado em
orientar a abertura correta de chamados.
"""
from services.embedding_service import generate_embedding
from services.vector_store import search
from services.llm_service import chat
from config.settings import TOP_K


SYSTEM_PROMPT_TEMPLATE = """Você é o assistente de abertura de chamados da empresa.

Seu único objetivo é orientar o colaborador sobre COMO resolver o problema dele:
- Se existe um passo a passo que a própria pessoa pode seguir para resolver sozinha
  (ex: resetar senha, liberar acesso simples), explique o passo a passo de forma clara,
  numerada e direta.
- Se o problema exige abertura de um chamado, informe qual é o chamado correto
  (nome/categoria) e, se houver, o link para abri-lo.
- Se o contexto trouxer as duas coisas (passo a passo E opção de chamado, caso o passo
  a passo não resolva), apresente ambos nessa ordem.

Regras importantes:
- Use APENAS as informações do contexto abaixo. Não invente links, nomes de chamados
  ou procedimentos que não estejam no contexto.
- Se a informação não estiver no contexto, diga claramente que não encontrou esse
  procedimento na base e sugira abrir um chamado genérico de TI para que a equipe
  oriente (sem inventar qual seria).
- Seja direto e objetivo. Nada de rodeios ou textos longos desnecessários.
- Se o pedido do colaborador for vago (ex: "meu computador não funciona"), faça UMA
  pergunta de esclarecimento antes de responder, em vez de chutar.

Contexto (trechos da base de conhecimento):
{context}
"""


def retrieve_context(question: str, index, chunks: list[dict]) -> str:
    if index is None or not chunks:
        return ""

    question_embedding = generate_embedding(question)
    positions = search(index, question_embedding, top_k=TOP_K)

    partes = []
    for pos in positions:
        if 0 <= pos < len(chunks):
            item = chunks[pos]
            partes.append(f"[Fonte: {item['source']}]\n{item['text']}")

    return "\n\n---\n\n".join(partes)


def build_system_prompt(context: str) -> str:
    if not context.strip():
        context = "(nenhum conteúdo relevante encontrado na base)"
    return SYSTEM_PROMPT_TEMPLATE.format(context=context)


def ask_question(question: str, index, chunks: list[dict], history: list[dict]) -> str:
    """
    history: histórico de mensagens JÁ TROCADAS até aqui (role/content),
    SEM incluir a pergunta atual. Esta função não modifica 'history' —
    apenas monta uma lista temporária para a chamada e retorna a resposta.
    Quem chamou é responsável por salvar a pergunta e a resposta no histórico.
    """
    context = retrieve_context(question, index, chunks)
    system_prompt = build_system_prompt(context)

    mensagens = [{"role": "system", "content": system_prompt}]
    mensagens += [m for m in history if m.get("role") != "system"]
    mensagens.append({"role": "user", "content": question})

    return chat(mensagens)
