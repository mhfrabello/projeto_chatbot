import streamlit as st
import ollama

# --- Configuração da página ---
st.set_page_config(
    page_title="Chat IA Local",
    page_icon="💬",
    layout="centered",
)

MODEL_NAME = "qwen2.5:7b"

SYSTEM_PROMPT = (
    "You are a friendly English conversation partner. "
    "Help the user practice English by chatting naturally, "
    "gently correcting mistakes when relevant, and keeping "
    "the conversation flowing with follow-up questions."
)

st.title("💬 Chat IA Local")
st.caption(f"Rodando localmente via Ollama · modelo: `{MODEL_NAME}`")

# --- Estado da sessão (histórico de mensagens) ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# --- Botão para limpar o chat ---
with st.sidebar:
    st.header("Configurações")
    st.write(f"**Modelo:** {MODEL_NAME}")
    if st.button("🗑️ Limpar conversa"):
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        st.rerun()

# --- Exibir histórico (ignorando a mensagem de sistema) ---
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Input do usuário ---
user_input = st.chat_input("Digite sua mensagem...")

# Exemplo de como fica a captura nativa de áudio no Streamlit:
audio_file = st.audio_input("Grave sua voz para conversar com a IA")

if audio_file is not None:
    st.audio(audio_file)
    # Aqui entraria o Whisper processando o 'audio_file'

if user_input:
    # Adiciona e exibe a mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Gera e exibe a resposta do modelo, com streaming
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        stream = ollama.chat(
            model=MODEL_NAME,
            messages=st.session_state.messages,
            stream=True,
        )

        for chunk in stream:
            content = chunk["message"]["content"]
            full_response += content
            placeholder.markdown(full_response + "▌")

        placeholder.markdown(full_response)

    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )