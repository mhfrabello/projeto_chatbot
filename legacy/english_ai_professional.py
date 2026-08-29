import streamlit as st
import ollama
import asyncio
import edge_tts
import io
import time
import re
import html
from faster_whisper import WhisperModel

# --- Configuração ---
st.set_page_config(page_title="Professor de Inglês IA", layout="centered")
MODEL_NAME = "qwen2.5:3b"
WHISPER_MODEL_SIZE = "small"
MAX_HISTORY_MESSAGES = 8  # quantas mensagens (user+assistant) manter no contexto, além do system prompt


def resetar_conversa():
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    st.session_state.audio_pendente = None
    st.session_state.turno = 0


def verificar_modelo_ollama(model_name: str) -> tuple[bool, str]:
    try:
        resposta = ollama.list()
        modelos = getattr(resposta, "models", None) or resposta.get("models", [])

        nomes = []
        for modelo in modelos:
            if hasattr(modelo, "model"):
                nomes.append(modelo.model)
            elif isinstance(modelo, dict):
                nomes.append(modelo.get("name") or modelo.get("model") or "")

        if any(model_name == nome or model_name in nome for nome in nomes):
            return True, ""

        return False, f"Modelo '{model_name}' não encontrado no Ollama. Rode: ollama pull {model_name}"
    except Exception as exc:
        return False, f"Não foi possível acessar o Ollama: {exc}"


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
    comunicador = edge_tts.Communicate(texto, "en-US-AvaNeural")
    buffer = io.BytesIO()
    async for chunk in comunicador.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    buffer.seek(0)
    return buffer.read()


# Regex para detectar fim de frase (. ! ?) seguido de espaço ou fim de string
FIM_DE_FRASE = re.compile(r"[.!?]+(?:\s|$)")


def extrair_frase_pronta(buffer_texto: str) -> tuple[str, str]:
    """
    Procura a última pontuação de fim de frase no buffer.
    Retorna (frase_pronta, resto_do_buffer). frase_pronta é "" se nada estiver pronto ainda.
    """
    matches = list(FIM_DE_FRASE.finditer(buffer_texto))
    if not matches:
        return "", buffer_texto
    ultimo_fim = matches[-1].end()
    return buffer_texto[:ultimo_fim].strip(), buffer_texto[ultimo_fim:]


async def gerar_audios_em_paralelo(frases: list[str]) -> list[bytes]:
    """Gera o áudio de cada frase em paralelo (todas as chamadas ao edge-tts
    disparadas ao mesmo tempo), o que é bem mais rápido que gerar uma por vez
    em sequência, sem a complexidade de sincronizar com o streaming do LLM."""
    return await asyncio.gather(*(gerar_audio_bytes(f) for f in frases))


def gerar_resposta_com_audio(mensagens_llm: list, model_name: str, placeholder) -> tuple[str, bytes]:
    """
    1) Consome o stream do Ollama normalmente, atualizando a UI em texto.
    2) Ao terminar, quebra a resposta em frases e gera o áudio de todas
       em paralelo (mais rápido que gerar uma por vez, e muito mais simples
       e confiável do que tentar sobrepor com o streaming de texto).
    """
    full_response = ""
    stream = ollama.chat(model=model_name, messages=mensagens_llm, stream=True)
    for chunk in stream:
        full_response += chunk["message"]["content"]
        placeholder.markdown(full_response + "▌")
    placeholder.markdown(full_response)

    # Quebra em frases para gerar os áudios em paralelo
    frases = []
    buffer_pendente = full_response
    while True:
        frase_pronta, buffer_pendente = extrair_frase_pronta(buffer_pendente)
        if not frase_pronta:
            break
        frases.append(frase_pronta)
    resto = buffer_pendente.strip()
    if resto:
        frases.append(resto)
    if not frases:
        frases = [full_response.strip()] if full_response.strip() else []

    if not frases:
        return full_response, b""

    try:
        audios = asyncio.run(gerar_audios_em_paralelo(frases))
    except RuntimeError as e:
        # Pode acontecer se já houver um event loop rodando no contexto do Streamlit.
        # Nesse caso, criamos um loop novo manualmente como alternativa.
        novo_loop = asyncio.new_event_loop()
        try:
            audios = novo_loop.run_until_complete(gerar_audios_em_paralelo(frases))
        finally:
            novo_loop.close()
    except Exception as e:
        st.error(f"Erro ao gerar áudio: {e}")
        return full_response, b""

    audio_bytes = b"".join(audios)
    return full_response, audio_bytes


def montar_mensagens_para_llm(mensagens: list) -> list:
    """System prompt fixo + apenas as últimas N mensagens, para não inflar o prompt a cada turno."""
    system_msg = mensagens[0]
    resto = mensagens[1:]
    janela = resto[-MAX_HISTORY_MESSAGES:] if len(resto) > MAX_HISTORY_MESSAGES else resto
    return [system_msg] + janela


# --- Estado ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "audio_pendente" not in st.session_state:
    st.session_state.audio_pendente = None
if "turno" not in st.session_state:
    st.session_state.turno = 0


# ============================================================
# FRONTEND PROFISSIONAL
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #09090b;
    --panel: #111114;
    --panel2: #17171b;
    --border: rgba(255,255,255,.08);
    --text: #f4f4f5;
    --muted: #a1a1aa;
    --accent: #8b5cf6;
    --accent2: #6366f1;
    --green: #22c55e;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

.stApp {
    background:
        radial-gradient(circle at 75% 0%, rgba(124,58,237,.14), transparent 30%),
        radial-gradient(circle at 10% 80%, rgba(59,130,246,.06), transparent 25%),
        var(--bg);
    color: var(--text);
}

#MainMenu, footer, header { visibility: hidden; }

.block-container {
    max-width: 1180px !important;
    padding: 1.2rem 2rem 2rem !important;
}

section[data-testid="stSidebar"] {
    background: rgba(14,14,17,.96);
    border-right: 1px solid var(--border);
}

section[data-testid="stSidebar"] > div {
    padding: 1.3rem 1rem;
}

.brand {
    display:flex;
    align-items:center;
    gap:12px;
    margin-bottom:28px;
}

.brand-icon {
    width:42px;
    height:42px;
    display:flex;
    align-items:center;
    justify-content:center;
    border-radius:13px;
    background:linear-gradient(135deg,#8b5cf6,#4f46e5);
    box-shadow:0 8px 30px rgba(124,58,237,.25);
    font-size:21px;
}

.brand-title {
    font-size:16px;
    font-weight:800;
    letter-spacing:-.4px;
}

.brand-sub {
    color:var(--muted);
    font-size:11px;
    margin-top:2px;
}

.side-label {
    color:#71717a;
    font-size:10px;
    font-weight:700;
    letter-spacing:1.2px;
    text-transform:uppercase;
    margin:22px 4px 9px;
}

.status {
    display:flex;
    align-items:center;
    gap:8px;
    color:#d4d4d8;
    font-size:12px;
}

.dot {
    width:7px;
    height:7px;
    border-radius:50%;
    background:var(--green);
    box-shadow:0 0 12px rgba(34,197,94,.7);
    display:inline-block;
}

.topbar {
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:5px 0 22px;
}

.page-title {
    font-size:25px;
    font-weight:800;
    letter-spacing:-.8px;
}

.page-subtitle {
    color:var(--muted);
    font-size:12px;
    margin-top:3px;
}

.online-pill {
    display:flex;
    align-items:center;
    gap:7px;
    padding:8px 12px;
    border:1px solid var(--border);
    background:rgba(255,255,255,.025);
    border-radius:999px;
    color:#d4d4d8;
    font-size:11px;
}

.hero {
    min-height:250px;
    border:1px solid var(--border);
    border-radius:24px;
    background:
        linear-gradient(135deg,rgba(139,92,246,.10),rgba(255,255,255,.02)),
        rgba(17,17,20,.8);
    display:flex;
    align-items:center;
    justify-content:center;
    text-align:center;
    padding:35px;
    margin-bottom:25px;
}

.hero-avatar {
    width:68px;
    height:68px;
    margin:0 auto 16px;
    border-radius:20px;
    display:flex;
    align-items:center;
    justify-content:center;
    background:linear-gradient(135deg,#8b5cf6,#4f46e5);
    font-size:31px;
    box-shadow:0 18px 50px rgba(124,58,237,.28);
}

.hero h1 {
    margin:0;
    font-size:30px;
    letter-spacing:-1px;
}

.hero p {
    color:var(--muted);
    margin:8px 0 0;
    font-size:13px;
}

.msg {
    max-width:78%;
    padding:13px 16px;
    border-radius:18px;
    font-size:14px;
    line-height:1.55;
    margin:10px 0;
}

.msg-ai {
    margin-right:auto;
    background:var(--panel2);
    border:1px solid var(--border);
    border-top-left-radius:5px;
}

.msg-user {
    margin-left:auto;
    background:linear-gradient(135deg,#7c3aed,#6366f1);
    border-top-right-radius:5px;
}

.msg-meta {
    color:#71717a;
    font-size:10px;
    margin-bottom:5px;
    font-weight:700;
    letter-spacing:.4px;
}

.msg-user .msg-meta {
    color:rgba(255,255,255,.7);
}

.metric {
    padding:11px;
    border:1px solid var(--border);
    border-radius:12px;
    background:rgba(255,255,255,.018);
    margin-bottom:8px;
}

.metric-value {
    font-weight:700;
    font-size:13px;
}

.metric-label {
    color:#71717a;
    font-size:9px;
    margin-top:2px;
}

.voice-card {
    border:1px solid var(--border);
    border-radius:18px;
    background:rgba(17,17,20,.75);
    padding:12px;
    margin-top:18px;
}

.voice-title {
    font-size:11px;
    font-weight:700;
    color:#d4d4d8;
    margin-bottom:7px;
}

.voice-sub {
    font-size:10px;
    color:#71717a;
}

.stButton > button {
    border-radius:12px !important;
    border:1px solid var(--border) !important;
    background:#18181b !important;
    color:#e4e4e7 !important;
}

.stButton > button:hover {
    border-color:rgba(139,92,246,.6) !important;
    color:white !important;
}

[data-testid="stChatInput"] textarea {
    background:#18181b !important;
    border:1px solid rgba(255,255,255,.08) !important;
    border-radius:15px !important;
    color:#fff !important;
}

[data-testid="stAudioInput"] {
    border:1px solid var(--border) !important;
    border-radius:14px !important;
    background:#18181b !important;
}

.stAlert {
    border-radius:14px !important;
}

div[data-testid="stExpander"] {
    background:rgba(255,255,255,.02);
    border:1px solid var(--border);
    border-radius:14px;
}

@media (max-width: 700px) {
    .block-container { padding:.8rem 1rem 1.5rem !important; }
    .hero { min-height:210px; }
    .msg { max-width:90%; }
    .page-title { font-size:21px; }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# ESTADO
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

if "audio_pendente" not in st.session_state:
    st.session_state.audio_pendente = None

if "turno" not in st.session_state:
    st.session_state.turno = 0

# ============================================================
# SIDEBAR
# ============================================================

modelo_ok, mensagem_modelo = verificar_modelo_ollama(MODEL_NAME)

with st.sidebar:
    st.markdown("""
    <div class="brand">
        <div class="brand-icon">🎙️</div>
        <div>
            <div class="brand-title">English AI</div>
            <div class="brand-sub">Your speaking companion</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="side-label">Workspace</div>', unsafe_allow_html=True)

    if st.button("＋  Nova conversa", use_container_width=True):
        resetar_conversa()
        st.rerun()

    if st.button("🗑️  Limpar conversa", use_container_width=True):
        resetar_conversa()
        st.rerun()

    st.markdown('<div class="side-label">Status</div>', unsafe_allow_html=True)

    if modelo_ok:
        st.markdown(
            '<div class="status"><span class="dot"></span> Ollama connected</div>',
            unsafe_allow_html=True
        )
    else:
        st.warning(mensagem_modelo)

    st.markdown('<div class="side-label">Model</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="metric"><div class="metric-value">{html.escape(MODEL_NAME)}</div>'
        '<div class="metric-label">LOCAL LLM</div></div>',
        unsafe_allow_html=True
    )

    user_message_count = sum(
        1 for m in st.session_state.messages
        if m["role"] == "user"
    )

    st.markdown('<div class="side-label">Session</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="metric"><div class="metric-value">{user_message_count} turns</div>'
        '<div class="metric-label">CURRENT SESSION</div></div>',
        unsafe_allow_html=True
    )

# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="topbar">
    <div>
        <div class="page-title">English AI</div>
        <div class="page-subtitle">Practice speaking naturally with your local AI tutor.</div>
    </div>
    <div class="online-pill">
        <span class="dot"></span>
        Local AI online
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# CHAT
# ============================================================

visible_messages = [
    m for m in st.session_state.messages
    if m["role"] != "system"
]

if not visible_messages:
    st.markdown("""
    <div class="hero">
        <div>
            <div class="hero-avatar">👨‍🏫</div>
            <h1>Let's practice English.</h1>
            <p>Speak naturally. Make mistakes. Get better.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

for msg in visible_messages:
    content = html.escape(msg["content"]).replace("\n", "<br>")

    if msg["role"] == "user":
        st.markdown(
            f'<div class="msg msg-user"><div class="msg-meta">YOU</div>{content}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="msg msg-ai"><div class="msg-meta">ENGLISH AI</div>{content}</div>',
            unsafe_allow_html=True
        )

# ============================================================
# AUDIO
# ============================================================

if st.session_state.audio_pendente:
    st.audio(
        st.session_state.audio_pendente,
        format="audio/mp3",
        autoplay=True
    )
    st.session_state.audio_pendente = None

# ============================================================
# INPUT
# ============================================================

st.markdown(
    '<div class="voice-card">'
    '<div class="voice-title">🎙️ Speak with your tutor</div>'
    '<div class="voice-sub">Record your voice or type below. Portuguese is okay when you get stuck.</div>'
    '</div>',
    unsafe_allow_html=True
)

audio_file = st.audio_input(
    "Gravar voz",
    key=f"audio_input_{st.session_state.turno}",
    label_visibility="collapsed"
)

user_input = st.chat_input(
    "Type in English or Portuguese..."
)

# ============================================================
# PROCESS AUDIO
# ============================================================

tempo_stt = None

if audio_file is not None:
    with st.spinner("Transcribing your voice..."):
        t0 = time.time()
        segments, _ = model.transcribe(audio_file)
        user_input = " ".join(s.text for s in segments)
        tempo_stt = time.time() - t0

    if user_input.strip():
        st.info(f"🗣️ You said: {user_input}")

# ============================================================
# PROCESS MESSAGE
# ============================================================

if user_input:
    modelo_ok, mensagem_modelo = verificar_modelo_ollama(MODEL_NAME)

    if not modelo_ok:
        st.error(mensagem_modelo)

    else:
        st.session_state.messages.append(
            {"role": "user", "content": user_input}
        )

        with st.chat_message("assistant"):
            placeholder = st.empty()

            mensagens_llm = montar_mensagens_para_llm(
                st.session_state.messages
            )

            t0 = time.time()

            try:
                full_response, audio_bytes = gerar_resposta_com_audio(
                    mensagens_llm,
                    MODEL_NAME,
                    placeholder
                )
            except Exception as exc:
                st.error(f"Erro ao conversar com o modelo: {exc}")
                full_response = "Sorry, there was an error generating the response."
                audio_bytes = b""

            tempo_llm_e_tts = time.time() - t0

            partes_tempo = []

            if tempo_stt is not None:
                partes_tempo.append(f"STT: {tempo_stt:.1f}s")

            partes_tempo.append(f"AI + TTS: {tempo_llm_e_tts:.1f}s")

            tempo_total = (tempo_stt or 0) + tempo_llm_e_tts
            partes_tempo.append(f"Total: {tempo_total:.1f}s")

            with st.expander("⚡ Performance details"):
                st.caption("  |  ".join(partes_tempo))

            if not audio_bytes:
                st.warning("Não foi possível gerar o áudio dessa resposta.")

        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )

        st.session_state.turno += 1
        st.session_state.audio_pendente = audio_bytes

        st.rerun()
