import streamlit as st
import ollama
import asyncio
import edge_tts
import os
import pygame
from faster_whisper import WhisperModel

# --- Configuração ---
st.set_page_config(page_title="Professor de Inglês IA", layout="centered")
MODEL_NAME = "qwen2.5:7b"
WHISPER_MODEL_SIZE = "small" # Se tiver RAM, pode trocar para "small"

# --- Inicialização do Whisper (carrega uma vez só) ---
@st.cache_resource
def load_whisper():
    return WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")

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
    "1. Keep responses relatively short and conversational, like a real conversation.\n"
    "2. Do not give long grammar lessons unless the user asks for one.\n"
    "3. Keep the conversation flowing naturally.\n"
    "4. Ask a relevant question at the end to encourage the user to continue speaking.\n"
)

st.title("👨‍🏫 Professor de Inglês IA")

# --- Função TTS ---
async def gerar_e_tocar_audio(texto):
    arquivo = "resposta_ia.mp3"
    comunicador = edge_tts.Communicate(texto, "en-US-JennyNeural")
    await comunicador.save(arquivo)
    
    pygame.mixer.init()
    pygame.mixer.music.load(arquivo)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.quit()
    if os.path.exists(arquivo): os.remove(arquivo)

# --- Estado ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# Sidebar
with st.sidebar:
    if st.button("🗑️ Limpar conversa"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()

# Exibir histórico
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- Entrada de Voz e Texto ---
st.divider()
audio_file = st.audio_input("🎙️ Gravar voz")
user_input = st.chat_input("Ou digite sua mensagem...")

# Processar entrada
if audio_file is not None:
    with open("temp_audio.wav", "wb") as f: f.write(audio_file.getvalue())
    with st.spinner("Transcrevendo..."):
        segments, _ = model.transcribe("temp_audio.wav")
        user_input = " ".join([s.text for s in segments])
    if os.path.exists("temp_audio.wav"): os.remove("temp_audio.wav")
    st.info(f"🗣️ Você disse: {user_input}")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        stream = ollama.chat(model=MODEL_NAME, messages=st.session_state.messages, stream=True)
        for chunk in stream:
            full_response += chunk["message"]["content"]
            placeholder.markdown(full_response + "▌")
        placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    asyncio.run(gerar_e_tocar_audio(full_response))