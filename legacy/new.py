import streamlit as st
import ollama
import asyncio
import edge_tts
import io
import time
import html
import re
from faster_whisper import WhisperModel

# --- Configuração ---
st.set_page_config(page_title="AI Language Tutor", layout="wide")
MODEL_NAME = "qwen2.5:3b"
WHISPER_MODEL_SIZE = "small"
MAX_HISTORY_MESSAGES = 8

# Configuração de Idiomas e Vozes
IDIOMAS = {
    "🇺🇸 English (US)": {
        "code": "en-US",
        "prompt": "The student is practicing American English. English is the main practice language, but every response must also contain natural Brazilian Portuguese."
    },
    "🇧🇷 Português (Brasil)": {
        "code": "pt-BR",
        "prompt": "The student is practicing Brazilian Portuguese. Portuguese is the main practice language, but every response should also contain natural English."
    },
    "🇫🇷 Français (France)": {
        "code": "fr-FR",
        "prompt": "The student is practicing French from France. French is the main practice language, but every response should also contain natural Brazilian Portuguese."
    },
    "🇪🇸 Español (España)": {
        "code": "es-ES",
        "prompt": "The student is practicing Spanish from Spain. Spanish is the main practice language, but every response should also contain natural Brazilian Portuguese."
    }
}

VOZES = {
    "en-US": {
        "Ava (F)": "en-US-AvaNeural", "Aria (F)": "en-US-AriaNeural", 
        "Emma (F)": "en-US-EmmaNeural", "Jenny (F)": "en-US-JennyNeural",
        "Andrew (M)": "en-US-AndrewNeural", "Guy (M)": "en-US-GuyNeural"
    },
    "pt-BR": {
        "Francisca (F)": "pt-BR-FranciscaNeural", "Thalita (F)": "pt-BR-ThalitaNeural",
        "Antonio (M)": "pt-BR-AntonioNeural"
    },
    "fr-FR": {
        "Denise (F)": "fr-FR-DeniseNeural", "Henri (M)": "fr-FR-HenriNeural"
    },
    "es-ES": {
        "Elvira (F)": "es-ES-ElviraNeural", "Alvaro (M)": "es-ES-AlvaroNeural"
    }
}

SYSTEM_PROMPT = (
    "You are a friendly, patient, conversational English teacher for a Brazilian student.\n\n"

    "LANGUAGE RULE - CRITICAL:\n"
    "Every normal response MUST contain BOTH English AND Brazilian Portuguese.\n"
    "Never respond entirely in English.\n"
    "Never respond entirely in Portuguese.\n"
    "English should be the main language, but Portuguese MUST appear naturally in every response.\n"
    "Mix English and Portuguese naturally instead of separating them into sections.\n"
    "Do not translate everything. Portuguese is only a support language.\n\n"

    "EXAMPLES:\n"
    "User: 'Tá, então bora praticar inglês.'\n"
    "Good response: 'Bora! Let's practice English then 😎 What did you do this morning?'\n\n"

    "User: 'Como eu posso dizer bom dia?'\n"
    "Good response: 'You can say \"Good morning!\" — é a forma mais comum de dizer bom dia. Now try saying it to me!'\n\n"

    "User: 'I woke up at 8 AM.'\n"
    "Good response: 'Nice! That sentence sounds perfect — ficou bem natural. What did you do after you woke up?'\n\n"

    "CONVERSATION:\n"
    "Keep responses short, normally 2-3 sentences.\n"
    "Sound like a real Brazilian English teacher, not a textbook.\n"
    "Be casual, natural, friendly, and encouraging.\n"
    "React to what the user actually said.\n"
    "Usually finish with a question that encourages the user to speak more.\n\n"

    "CORRECTIONS:\n"
    "Correct genuine English grammar, vocabulary, and naturalness mistakes.\n"
    "Do not overcorrect small mistakes.\n"
    "Keep corrections brief.\n"
    "Show a natural corrected version when useful.\n\n"

    "WHISPER TRANSCRIPTION:\n"
    "User messages may come from Whisper speech-to-text and may contain transcription errors.\n"
    "Do not assume strange or nonsensical words were actually spoken.\n"
    "Use context to infer what the user intended.\n"
    "If the intended meaning is obvious, correct the intended sentence rather than the corrupted transcription.\n"
    "If you cannot confidently understand the intended meaning, ask for clarification.\n"
    "Never invent grammar corrections based on obvious transcription errors.\n\n"

    "FINAL RULE:\n"
    "Before answering, make sure the response contains BOTH English AND Brazilian Portuguese. "
    "If it does not, rewrite it."
)

# --- Funções de Estado ---
def resetar_conversa():
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    st.session_state.audio_pendente = None
    st.session_state.turno = 0
    st.session_state.ultimo_audio_processado = None

@st.cache_resource
def load_whisper():
    return WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8", cpu_threads=6)

model = load_whisper()

# --- Funções de TTS e LLM ---
async def gerar_audio_completo(texto: str, voz: str) -> bytes:
    comunicador = edge_tts.Communicate(texto, voz)
    buffer = io.BytesIO()
    async for chunk in comunicador.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    return buffer.getvalue()

def processar_resposta_llm(mensagens, model_name, idioma_prompt, voice_id):
    full_response = ""
    msgs = [{"role": "system", "content": SYSTEM_PROMPT + f"\n\nCURRENT TARGET LANGUAGE: {idioma_prompt}\nVOICE OUTPUT: Your answer will be spoken aloud. Keep it natural."}] + mensagens[1:]
    
    stream = ollama.chat(model=model_name, messages=msgs, stream=True)
    for chunk in stream:
        content = chunk["message"]["content"]
        full_response += content
        yield full_response

    try:
        audio_bytes = asyncio.run(gerar_audio_completo(full_response, voice_id))
        st.session_state.audio_pendente = audio_bytes
    except Exception as e:
        st.error(f"TTS Error: {e}")

# --- Frontend CSS ---
st.markdown("""
<style>
:root { --bg: #09090b; --accent: #8b5cf6; }
.stApp { background: var(--bg); color: #e4e4e7; }
.msg-ai { background: #18181b; padding: 15px; border-radius: 12px; border: 1px solid #27272a; margin-bottom: 10px; }
.msg-user { background: #2e1065; padding: 15px; border-radius: 12px; margin-bottom: 10px; }
.sidebar-content { padding: 10px; }
</style>
""", unsafe_allow_html=True)

# --- Inicialização do Estado ---
if "messages" not in st.session_state: resetar_conversa()
if "audio_pendente" not in st.session_state: st.session_state.audio_pendente = None
if "turno" not in st.session_state: st.session_state.turno = 0
if "ultimo_audio_processado" not in st.session_state: st.session_state.ultimo_audio_processado = None

# --- Sidebar ---
with st.sidebar:
    st.title("Settings")
    lang_key = st.selectbox("Language", list(IDIOMAS.keys()))
    lang_info = IDIOMAS[lang_key]
    
    voz_nome = st.selectbox("Voice", list(VOZES[lang_info["code"]].keys()))
    voz_id = VOZES[lang_info["code"]][voz_nome]
    
    if st.button("New Conversation"): 
        resetar_conversa()
        st.rerun()

# --- Chat Logic (Renderização do Histórico) ---
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- Inputs ---
audio_file = st.audio_input("Record", key=f"audio_input_{st.session_state.turno}")
prompt = st.chat_input("Say something...")

user_input = None

# Tratamento seguro do Áudio para evitar Loop Infinito
if audio_file is not None:
    audio_bytes_data = audio_file.getvalue()
    if audio_bytes_data != st.session_state.ultimo_audio_processado:
        st.session_state.ultimo_audio_processado = audio_bytes_data
        with st.spinner("Transcribing..."):
            segments, _ = model.transcribe(audio_file)
            user_input = " ".join(s.text for s in segments)

if prompt:
    user_input = prompt

# --- Processamento de Mensagem ---
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_text = ""
        for chunk in processar_resposta_llm(st.session_state.messages, MODEL_NAME, lang_info["prompt"], voz_id):
            placeholder.markdown(chunk + "▌")
            full_text = chunk
        placeholder.markdown(full_text)
        st.session_state.messages.append({"role": "assistant", "content": full_text})
        st.session_state.turno += 1
        st.rerun()

if st.session_state.audio_pendente:
    st.audio(st.session_state.audio_pendente, format="audio/mp3", autoplay=True)
    st.session_state.audio_pendente = None