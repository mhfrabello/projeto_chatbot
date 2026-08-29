import streamlit as st
import ollama
import asyncio
import edge_tts
import io
import time

from faster_whisper import WhisperModel


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="AI Language Tutor",
    page_icon="🗣️",
    layout="centered",
)

MODEL_NAME = "qwen2.5:3b"
WHISPER_MODEL_SIZE = "small"
MAX_HISTORY_MESSAGES = 10

# Limita o tamanho das respostas para manter a conversa rápida.
LLM_OPTIONS = {
    "temperature": 0.6,
    "top_p": 0.9,
    "num_predict": 120,
}

SYSTEM_PROMPT = (
    "You are a friendly, patient language conversation partner. "
    "Chat naturally with the user in whatever language they use. "
    "If they mix Portuguese and English, feel free to mix too. "
    "Gently correct mistakes when relevant, keep answers short "
    "(1-3 sentences) and ask a follow-up question to keep the "
    "conversation going."
)

VOZES = {
    "Emma (F, US)": "en-US-EmmaMultilingualNeural",
    "Andrew (M, US)": "en-US-AndrewMultilingualNeural",
    "Brian (M, US)": "en-US-BrianMultilingualNeural",
}


# ============================================================
# CARREGAMENTO DE RECURSOS (cacheado)
# ============================================================

@st.cache_resource
def carregar_whisper():
    return WhisperModel(
        WHISPER_MODEL_SIZE,
        device="cpu",
        compute_type="int8",
        cpu_threads=6,
    )


whisper_model = carregar_whisper()


# ============================================================
# FUNÇÕES
# ============================================================

def transcrever_audio(audio_file) -> str:
    segmentos, _ = whisper_model.transcribe(
        audio_file,
        beam_size=5,
        vad_filter=True,
    )
    return " ".join(seg.text for seg in segmentos).strip()


def gerar_resposta(historico) -> tuple[str, float]:
    mensagens = [{"role": "system", "content": SYSTEM_PROMPT}]
    mensagens.extend(historico[-MAX_HISTORY_MESSAGES:])

    inicio = time.perf_counter()

    resposta = ollama.chat(
        model=MODEL_NAME,
        messages=mensagens,
        stream=False,
        options=LLM_OPTIONS,
        keep_alive="5m",
    )

    tempo = time.perf_counter() - inicio
    texto = resposta["message"]["content"].strip()

    return texto, tempo


async def gerar_audio(texto: str, voz: str) -> bytes:
    comunicador = edge_tts.Communicate(texto, voz)
    buffer = io.BytesIO()

    async for chunk in comunicador.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])

    return buffer.getvalue()


def resetar_conversa():
    st.session_state.messages = []
    st.session_state.audio_pendente = None
    st.session_state.turno = 0
    st.session_state.ultimo_audio_processado = None


# ============================================================
# ESTADO INICIAL
# ============================================================

if "messages" not in st.session_state:
    resetar_conversa()

if "audio_pendente" not in st.session_state:
    st.session_state.audio_pendente = None

if "turno" not in st.session_state:
    st.session_state.turno = 0

if "ultimo_audio_processado" not in st.session_state:
    st.session_state.ultimo_audio_processado = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("🗣️ AI Language Tutor")
    st.caption(f"Modelo: `{MODEL_NAME}` · Whisper: `{WHISPER_MODEL_SIZE}`")

    st.divider()

    voz_nome = st.selectbox("Voz", list(VOZES.keys()))
    voz_id = VOZES[voz_nome]

    st.divider()

    if st.button("🗑️ Nova conversa", use_container_width=True):
        resetar_conversa()
        st.rerun()


# ============================================================
# HISTÓRICO NA TELA
# ============================================================

st.title("Pratique idiomas conversando")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ============================================================
# INPUT (voz ou texto)
# ============================================================

audio_file = st.audio_input(
    "Grave sua voz",
    key=f"audio_input_{st.session_state.turno}",
)

prompt = st.chat_input("Ou digite algo...")

user_input = None

if audio_file is not None:
    audio_bytes = audio_file.getvalue()

    if audio_bytes != st.session_state.ultimo_audio_processado:
        st.session_state.ultimo_audio_processado = audio_bytes

        with st.spinner("Transcrevendo..."):
            user_input = transcrever_audio(audio_file)

if prompt:
    user_input = prompt.strip()


# ============================================================
# PROCESSAMENTO DO TURNO
# ============================================================

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            resposta, tempo_llm = gerar_resposta(st.session_state.messages)

        st.markdown(resposta)
        st.caption(f"LLM: {tempo_llm:.2f}s")

        st.session_state.messages.append(
            {"role": "assistant", "content": resposta}
        )

        try:
            with st.spinner("Gerando áudio..."):
                inicio_tts = time.perf_counter()
                audio_bytes = asyncio.run(gerar_audio(resposta, voz_id))
                tempo_tts = time.perf_counter() - inicio_tts

            st.session_state.audio_pendente = audio_bytes
            st.caption(f"TTS: {tempo_tts:.2f}s")

        except Exception as e:
            st.error(f"Erro ao gerar áudio: {e}")

        st.session_state.turno += 1
        st.rerun()


# ============================================================
# REPRODUÇÃO DE ÁUDIO
# ============================================================

if st.session_state.audio_pendente:
    st.audio(st.session_state.audio_pendente, format="audio/mp3", autoplay=True)
    st.session_state.audio_pendente = None