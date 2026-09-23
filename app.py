# app.py
"""
Assistente de TI — orientação para abertura de chamados, com RAG sobre a
base de conhecimento em knowledge/base_conhecimento.md.
"""
import streamlit as st

from services.knowledge_base import build_knowledge_base, KnowledgeBaseError
from services.rag_service import ask_question
from services.llm_service import LLMError
from components.styles import CUSTOM_CSS
from components.chat_ui import render_header, render_empty_state
from components.sidebar import render_sidebar
from config.settings import APP_TITLE, KNOWLEDGE_DIR

st.set_page_config(page_title=APP_TITLE, page_icon="🎫", layout="centered")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_resource(show_spinner="Carregando base de conhecimento...")
def get_knowledge_base():
    return build_knowledge_base()


def limpar_conversa():
    st.session_state.messages = []
    st.rerun()


def recarregar_base():
    st.cache_resource.clear()
    st.rerun()


def processar_pergunta(pergunta: str, index, chunks: list[dict]):
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando a base de conhecimento..."):
            try:
                resposta = ask_question(pergunta, index, chunks, st.session_state.messages)
            except LLMError as erro:
                resposta = None
                st.markdown(
                    f'<div class="aviso-erro">⚠️ Não consegui obter uma resposta agora. '
                    f'{erro}</div>',
                    unsafe_allow_html=True,
                )
            except Exception:
                resposta = None
                st.markdown(
                    '<div class="aviso-erro">⚠️ Algo deu errado ao processar sua pergunta. '
                    "Tente novamente em instantes ou abra um chamado geral de TI descrevendo "
                    "o problema.</div>",
                    unsafe_allow_html=True,
                )

        if resposta:
            st.markdown(resposta)

    st.session_state.messages.append({"role": "user", "content": pergunta})
    if resposta:
        st.session_state.messages.append({"role": "assistant", "content": resposta})


def main():
    render_header(APP_TITLE)

    try:
        index, chunks, num_entradas = get_knowledge_base()
        erro_base = None
    except KnowledgeBaseError as erro:
        index, chunks, num_entradas = None, [], 0
        erro_base = str(erro)

    if erro_base:
        st.markdown(
            f'<div class="aviso-erro">⚠️ Não foi possível carregar a base de conhecimento.'
            f'<br><br><b>Detalhe:</b> {erro_base}'
            f'<br><br>Verifique a configuração do Azure OpenAI no arquivo <code>.env</code> '
            f'e clique em "Recarregar base de conhecimento" na barra lateral após corrigir.'
            f"</div>",
            unsafe_allow_html=True,
        )
        render_sidebar(0, 0, on_reload=recarregar_base, on_clear=limpar_conversa)
        return

    if num_entradas == 0:
        st.markdown(
            f'<div class="aviso-vazio">📄 Nenhum conteúdo encontrado em '
            f'<code>{KNOWLEDGE_DIR}/</code>. Adicione o arquivo '
            f'<code>base_conhecimento.md</code> com os procedimentos e clique em '
            f'"Recarregar base de conhecimento".</div>',
            unsafe_allow_html=True,
        )
        render_sidebar(0, 0, on_reload=recarregar_base, on_clear=limpar_conversa)
        return

    render_sidebar(num_entradas, len(chunks), on_reload=recarregar_base, on_clear=limpar_conversa)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    pergunta_do_exemplo = None
    if not st.session_state.messages:
        pergunta_do_exemplo = render_empty_state()

    for message in st.session_state.messages:
        if message["role"] == "system":
            continue
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    pergunta_digitada = st.chat_input("Descreva o problema que você está enfrentando...")

    if pergunta_do_exemplo:
        processar_pergunta(pergunta_do_exemplo, index, chunks)
    elif pergunta_digitada:
        processar_pergunta(pergunta_digitada, index, chunks)


if __name__ == "__main__":
    main()
