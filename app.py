# app.py
"""
Assistente de abertura de chamados — chat com RAG sobre a base de
conhecimento em knowledge/.
"""
import streamlit as st

from services.knowledge_base import build_knowledge_base
from services.rag_service import ask_question
from config.settings import APP_TITLE, KNOWLEDGE_DIR

st.set_page_config(page_title=APP_TITLE, page_icon="🎫", layout="centered")


@st.cache_resource(show_spinner="Carregando base de conhecimento...")
def get_knowledge_base():
    return build_knowledge_base()


def main():
    st.title(f"🎫 {APP_TITLE}")
    st.caption(
        "Me conte o que você precisa fazer que eu te digo se dá pra resolver "
        "sozinho ou qual chamado abrir."
    )

    index, chunks, num_documentos = get_knowledge_base()

    if num_documentos == 0:
        st.warning(
            f"Nenhum documento encontrado na pasta `{KNOWLEDGE_DIR}/`. "
            "Adicione arquivos .md, .txt ou .pdf com os procedimentos e "
            "reinicie o app."
        )
        return

    with st.sidebar:
        st.metric("Documentos carregados", num_documentos)
        st.metric("Trechos indexados", len(chunks))
        if st.button("🔄 Recarregar base de conhecimento"):
            st.cache_resource.clear()
            st.rerun()
        st.divider()
        if st.button("🗑️ Limpar conversa"):
            st.session_state.messages = []
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        if message["role"] == "system":
            continue
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    pergunta = st.chat_input("Ex: quero instalar um programa novo, o que eu faço?")

    if pergunta:
        with st.chat_message("user"):
            st.markdown(pergunta)

        with st.chat_message("assistant"):
            with st.spinner("Consultando a base de conhecimento..."):
                resposta = ask_question(
                    pergunta, index, chunks, st.session_state.messages
                )
            st.markdown(resposta)

        st.session_state.messages.append({"role": "user", "content": pergunta})
        st.session_state.messages.append({"role": "assistant", "content": resposta})


if __name__ == "__main__":
    main()
