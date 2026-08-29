import streamlit as st
import ollama
import asyncio
import edge_tts
import io
import time
import re
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
    comunicador = edge_tts.Communicate(texto, "en-US-JennyNeural")
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

# Sidebar
with st.sidebar:
    st.header("Configurações")
    modelo_ok, mensagem_modelo = verificar_modelo_ollama(MODEL_NAME)
    if modelo_ok:
        st.success(f"Modelo Ollama pronto: {MODEL_NAME}")
    else:
        st.warning(mensagem_modelo)

    if st.button("🗑️ Limpar conversa"):
        resetar_conversa()
        st.rerun()
    st.caption(f"Contexto enviado ao modelo: system prompt + últimas {MAX_HISTORY_MESSAGES} mensagens")

# --- Entrada de Voz e Texto (fica embaixo, junto ao histórico já exibido) ---
st.divider()

# Exibir histórico primeiro, para o gravador ficar sempre no rodapé
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Se há um áudio pendente de uma resposta recém-gerada (via rerun), toca ele agora,
# já na posição correta (logo após a última mensagem do histórico acima).
if st.session_state.audio_pendente:
    st.audio(st.session_state.audio_pendente, format="audio/mp3", autoplay=True)
    st.session_state.audio_pendente = None  # consome, para não tocar de novo em reruns futuros

st.caption("🎙️ Clique para gravar, fale, clique de novo para parar, e confirme o envio. "
           "Assim que a resposta terminar, o gravador já fica pronto para o próximo turno.")
audio_file = st.audio_input("Gravar voz", key=f"audio_input_{st.session_state.turno}", label_visibility="collapsed")
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
    modelo_ok, mensagem_modelo = verificar_modelo_ollama(MODEL_NAME)
    if not modelo_ok:
        st.error(mensagem_modelo)
    else:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            mensagens_llm = montar_mensagens_para_llm(st.session_state.messages)

            t0 = time.time()
            try:
                full_response, audio_bytes = gerar_resposta_com_audio(mensagens_llm, MODEL_NAME, placeholder)
            except Exception as exc:
                st.error(f"Erro ao conversar com o modelo: {exc}")
                full_response = "Desculpe, houve um erro ao gerar a resposta."
                audio_bytes = b""
            tempo_llm_e_tts = time.time() - t0

            if not audio_bytes:
                st.warning("⚠️ Não foi possível gerar o áudio dessa resposta.")

            # Resumo de latência: LLM completo + TTS das frases em paralelo
            partes_tempo = []
            if tempo_stt is not None:
                partes_tempo.append(f"STT: {tempo_stt:.1f}s")
            partes_tempo.append(f"LLM+TTS: {tempo_llm_e_tts:.1f}s")
            tempo_total = (tempo_stt or 0) + tempo_llm_e_tts
            partes_tempo.append(f"Total: {tempo_total:.1f}s")
            st.caption("⏱️ " + " | ".join(partes_tempo))

        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.turno += 1
        # Guarda o áudio para tocar na PRÓXIMA renderização (após o rerun), já na posição
        # correta do histórico — assim o layout fica certo E o áudio consegue tocar.
        st.session_state.audio_pendente = audio_bytes
        st.rerun()