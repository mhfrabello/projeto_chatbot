import streamlit as st
import ollama
import asyncio
import edge_tts
import io
import time
from faster_whisper import WhisperModel

# --- Configuração ---
st.set_page_config(page_title="Professor de Inglês IA", layout="centered")
MODEL_NAME = "qwen2.5:7b"
WHISPER_MODEL_SIZE = "small"
MAX_HISTORY_MESSAGES = 8  # quantas mensagens (user+assistant) manter no contexto, além do system prompt

# --- Inicialização do Whisper (carrega uma vez só) ---
@st.cache_resource
def load_whisper():
    return WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8", cpu_threads=6)

model = load_whisper()

SYSTEM_PROMPT = (
    "You are an expert, friendly, patient, and conversational bilingual English teacher. "
    "Your primary goal is to help the user practice spoken English naturally and confidently.\n\n"

    "IMPORTANT CONTEXT:\n"
    "The user's messages may come from speech-to-text transcription using Whisper. "
    "The transcription can contain mistakes, especially with English words, pronunciation, "
    "accent, mixed Portuguese/English speech, or background noise. "
    "Therefore, NEVER assume that every strange word or sentence in the transcription "
    "was actually spoken by the user.\n\n"

    "TRANSCRIPTION ERROR HANDLING:\n"
    "1. If the transcription is clear and coherent, treat it normally.\n"
    "2. If the transcription contains strange, nonsensical, or contextually impossible words, "
    "consider that they may be transcription errors rather than English mistakes.\n"
    "3. Use the surrounding context to infer what the user most likely intended to say.\n"
    "4. If you can confidently infer the intended sentence, briefly mention the likely interpretation "
    "instead of correcting the corrupted transcription as if it were the user's actual speech.\n"
    "5. Example: if the transcription says 'Eu quero praticar um pouco bem doleis. Consegui mais de dar.' "
    "but the likely intended meaning is 'Eu quero praticar um pouco de inglês, consegue me ajudar?', "
    "do NOT correct 'bem doleis' or invent grammatical explanations. Instead say something like: "
    "'I think you meant: Eu quero praticar um pouco de inglês, consegue me ajudar?' "
    "Then provide the natural English version.\n"
    "6. If you are not confident about what the user meant, ask for clarification instead of guessing.\n\n"

    "LANGUAGE PRACTICE:\n"
    "1. Encourage the user to speak primarily in English.\n"
    "2. The user may switch to Portuguese whenever they don't know how to express something in English.\n"
    "3. When the user uses Portuguese because they don't know an English word or phrase, "
    "help them translate it naturally into English.\n"
    "4. Do not force the user to speak English when they are explicitly asking for an explanation in Portuguese.\n"
    "5. Use Portuguese briefly when necessary to explain a correction, then return to English practice.\n\n"

    "CORRECTIONS:\n"
    "1. Correct genuine English grammar, vocabulary, pronunciation-related wording, and naturalness issues.\n"
    "2. Do not overcorrect every small mistake.\n"
    "3. Prioritize mistakes that would make the user's English unclear or unnatural.\n"
    "4. When correcting, show the user's intended sentence and a natural corrected version.\n"
    "5. Never invent an error that was caused by speech-to-text transcription.\n\n"

    "CONVERSATION STYLE:\n"
    "1. HARD LIMIT: your entire response must be 2-3 sentences maximum, unless the user "
    "explicitly asks for a detailed explanation (e.g. 'explain more', 'why is that wrong').\n"
    "2. Do not give long grammar lessons unless the user asks for one.\n"
    "3. Keep the conversation flowing naturally, like real spoken dialogue, not a written essay.\n"
    "4. Ask a relevant question at the end to encourage the user to continue speaking.\n"
    "5. If you have more to say, hold back and let the conversation continue naturally instead "
    "of packing everything into one response.\n"
)

st.title("👨‍🏫 Professor de Inglês IA")


# --- Função TTS: gera bytes em memória, sem salvar em disco e sem bloquear em playback ---
async def gerar_audio_bytes(texto: str) -> bytes:
    comunicador = edge_tts.Communicate(texto, "en-US-JennyNeural")
    buffer = io.BytesIO()
    async for chunk in comunicador.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    buffer.seek(0)
    return buffer.read()


def montar_mensagens_para_llm(mensagens: list) -> list:
    """System prompt fixo + apenas as últimas N mensagens, para não inflar o prompt a cada turno."""
    system_msg = mensagens[0]
    resto = mensagens[1:]
    janela = resto[-MAX_HISTORY_MESSAGES:] if len(resto) > MAX_HISTORY_MESSAGES else resto
    return [system_msg] + janela


# --- Estado ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# Sidebar
with st.sidebar:
    if st.button("🗑️ Limpar conversa"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()
    st.caption(f"Contexto enviado ao modelo: system prompt + últimas {MAX_HISTORY_MESSAGES} mensagens")

# Exibir histórico
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- Entrada de Voz e Texto ---
st.divider()
audio_file = st.audio_input("🎙️ Gravar voz")
user_input = st.chat_input("Ou digite sua mensagem...")

# Processar entrada de áudio (transcrição direto do buffer, sem salvar em disco)
tempo_stt = None
if audio_file is not None:
    with st.spinner("Transcrevendo..."):
        t0 = time.time()
        segments, _ = model.transcribe(audio_file)
        user_input = " ".join([s.text for s in segments])
        tempo_stt = time.time() - t0
    st.info(f"🗣️ Você disse: {user_input}")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        mensagens_llm = montar_mensagens_para_llm(st.session_state.messages)

        t0 = time.time()
        stream = ollama.chat(model=MODEL_NAME, messages=mensagens_llm, stream=True)
        for chunk in stream:
            full_response += chunk["message"]["content"]
            placeholder.markdown(full_response + "▌")
        placeholder.markdown(full_response)
        tempo_llm = time.time() - t0

        # Gera o áudio e toca via componente nativo do navegador, sem travar a UI esperando playback
        with st.spinner("Gerando áudio..."):
            t0 = time.time()
            audio_bytes = asyncio.run(gerar_audio_bytes(full_response))
            tempo_tts = time.time() - t0
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)

        # Resumo de latência por etapa, para identificar gargalos reais
        partes_tempo = []
        if tempo_stt is not None:
            partes_tempo.append(f"STT: {tempo_stt:.1f}s")
        partes_tempo.append(f"LLM: {tempo_llm:.1f}s")
        partes_tempo.append(f"TTS: {tempo_tts:.1f}s")
        tempo_total = (tempo_stt or 0) + tempo_llm + tempo_tts
        partes_tempo.append(f"Total: {tempo_total:.1f}s")
        st.caption("⏱️ " + " | ".join(partes_tempo))

    st.session_state.messages.append({"role": "assistant", "content": full_response})