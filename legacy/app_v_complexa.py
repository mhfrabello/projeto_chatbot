import streamlit as st
import ollama
import asyncio
import edge_tts
import io
import re
import time
import unicodedata

from faster_whisper import WhisperModel


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="AI Language Tutor",
    layout="wide"
)

MODEL_NAME = "qwen2.5:3b"

WHISPER_MODEL_SIZE = "small"

MAX_HISTORY_MESSAGES = 10

# Limita o tamanho das respostas para manter a conversa rápida.
LLM_OPTIONS = {
    "temperature": 0.55,
    "top_p": 0.9,
    "num_predict": 120,
    "repeat_penalty": 1.05,
}

# Modo inicial.
#
# English Only = foco total em conversação.
# Bilingual = mistura natural de inglês + português.
DEFAULT_MODE = "english_only"


# ============================================================
# IDIOMAS
# ============================================================

IDIOMAS = {
    "🇺🇸 English (US)": {
        "code": "en-US",
        "name": "American English",
        "prompt": (
            "The target practice language is American English. "
            "The student is Brazilian."
        ),
    },

    "🇧🇷 Português (Brasil)": {
        "code": "pt-BR",
        "name": "Brazilian Portuguese",
        "prompt": (
            "The target practice language is Brazilian Portuguese. "
            "The student is Brazilian."
        ),
    },

    "🇫🇷 Français (France)": {
        "code": "fr-FR",
        "name": "French from France",
        "prompt": (
            "The target practice language is French from France. "
            "The student is Brazilian."
        ),
    },

    "🇪🇸 Español (España)": {
        "code": "es-ES",
        "name": "Spanish from Spain",
        "prompt": (
            "The target practice language is Spanish from Spain. "
            "The student is Brazilian."
        ),
    },
}


# ============================================================
# VOZES MULTILÍNGUES
# ============================================================

VOZES = {
    "Emma Multilingual (F)": "en-US-EmmaMultilingualNeural",
    "Ava Multilingual (F)": "en-US-AvaMultilingualNeural",
    "Andrew Multilingual (M)": "en-US-AndrewMultilingualNeural",
    "Brian Multilingual (M)": "en-US-BrianMultilingualNeural",
}


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are a friendly, patient, natural and conversational language teacher.

You are helping a Brazilian student practice a foreign language,
especially spoken English.

Your job is to have a REAL conversation, not to give textbook lessons.

Keep responses short, natural and easy to speak aloud.

==================================================
CONVERSATION MODE
==================================================

The application controls the conversation mode.

There are two modes:

1. ENGLISH ONLY
2. BILINGUAL SUPPORT

You MUST obey the current mode.

Do not decide the mode yourself.

==================================================
ENGLISH ONLY MODE
==================================================

In ENGLISH ONLY mode:

- Respond entirely in the target practice language.
- When the target language is English, respond 100% in English.
- Do not use Brazilian Portuguese unless the user specifically
  asks for an explanation or translation.
- Keep the conversation natural and conversational.
- Do not mention that you are following a mode.

Example:

User:
"Let's speak English."

Good:
"Sure! Let's speak only English. What did you do today?"

==================================================
BILINGUAL SUPPORT MODE
==================================================

In BILINGUAL SUPPORT mode:

- The target practice language is dominant.
- Brazilian Portuguese is used as support.
- Mix both languages naturally.
- Do not create separate language sections.
- Do not translate every sentence.
- Portuguese should provide clarification, encouragement,
  reactions, or explanations.

Example:

"Nice! That sentence sounds natural — ficou bem legal. What did you do next?"

Another example:

"You can say 'I was on my phone' — essa é uma forma bem natural de falar isso. Try the full sentence."

==================================================
LANGUAGE PRACTICE
==================================================

The student may speak English, Portuguese, or a mixture.

If the student does not know how to say something:

- understand the Portuguese expression;
- provide the natural target-language expression;
- continue the conversation.

Example:

User:
"Como fala 'fiquei em casa'?"

Good:
"You can say 'I stayed home.' É uma frase bem comum. What did you do while you were home?"

Do not give long grammar explanations unless requested.

==================================================
CORRECTIONS
==================================================

Correct real language mistakes.

Prioritize:

- grammar
- vocabulary
- word choice
- naturalness
- clarity

Do not correct every tiny mistake.

Prefer natural corrections.

Example:

User:
"I have 26 years."

Good:
"In English, we'd say 'I'm 26 years old.' It's a very common mistake for Portuguese speakers."

Then continue the conversation.

==================================================
WHISPER
==================================================

The user's input may come from Whisper speech-to-text.

Whisper can make mistakes due to:

- pronunciation
- accent
- background noise
- similar sounds
- mixed languages

Never assume that a strange transcription is necessarily
a real language mistake.

If a transcription is clearly corrupted:

- infer the likely intent when possible;
- do not invent a grammar explanation;
- ask for clarification if the intended meaning is unclear.

Example:

Whisper:
"Eu quero praticar um pouco bem doleis."

Likely intent:
"Eu quero praticar um pouco de inglês."

Good response:

"I think Whisper got that part wrong 😅 — você provavelmente quis dizer
'de inglês'. In English, you can say 'I want to practice some English.'"

==================================================
STYLE
==================================================

Normally respond in 1-3 sentences.

Be:

- casual
- warm
- natural
- patient
- encouraging

Avoid:

- robotic language
- generic filler
- long explanations
- excessive repetition
- unnecessary headings

Talk like a real teacher having a conversation.

Usually ask a short follow-up question to keep the student speaking.

==================================================
IMPORTANT
==================================================

The application controls the conversation mode.

Follow the provided CURRENT CONVERSATION MODE exactly.

Do not override it.

Do not explain the mode to the student unless asked.
"""


# ============================================================
# NORMALIZAÇÃO DE TEXTO
# ============================================================

def normalizar_texto(texto: str) -> str:
    """
    Remove acentos e coloca tudo em lowercase.
    Ajuda a reconhecer frases como:

    "em português você fala também"
    "em portugues voce fala tambem"
    """

    texto = texto.lower().strip()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        char
        for char in texto
        if unicodedata.category(char) != "Mn"
    )

    return texto


# ============================================================
# DETECTOR DE PEDIDO DE ENGLISH ONLY
# ============================================================

def usuario_pediu_ingles(texto: str) -> bool:

    texto = normalizar_texto(texto)

    padroes = [

        r"\bspeak english\b",
        r"\bspeak in english\b",
        r"\bspeak only english\b",
        r"\benglish only\b",
        r"\bonly english\b",
        r"\benglish please\b",
        r"\bspeak english please\b",
        r"\btalk to me in english\b",
        r"\blets speak english\b",
        r"\blets talk in english\b",
        r"\bcan we speak english\b",
        r"\bcan we speak only english\b",
        r"\bstop speaking portuguese\b",
        r"\bno portuguese\b",
        r"\bwithout portuguese\b",
        r"\bspoken english please\b",

        r"\bso ingles\b",
        r"\bso english\b",
        r"\bso em ingles\b",
        r"\bapenas ingles\b",
        r"\bsomente ingles\b",
        r"\bsomente em ingles\b",
        r"\bfala so ingles\b",
        r"\bfala somente ingles\b",
        r"\bfale so ingles\b",
        r"\bfale somente ingles\b",
        r"\bquero falar ingles\b",
        r"\bquero falar so ingles\b",
        r"\bvamos falar ingles\b",
        r"\bagora so ingles\b",
        r"\bagora somente ingles\b",
        r"\bagora em ingles\b",
        r"\bso em ingles\b",
    ]

    return any(
        re.search(padrao, texto)
        for padrao in padroes
    )


# ============================================================
# DETECTOR DE PEDIDO DE BILINGUAL
# ============================================================

def usuario_pediu_bilingue(texto: str) -> bool:

    texto = normalizar_texto(texto)

    padroes = [

        # Português
        r"\bfala portugues tambem\b",
        r"\bfale portugues tambem\b",
        r"\bportugues tambem\b",
        r"\bem portugues voce fala tambem\b",
        r"\bem portugues fala tambem\b",
        r"\bvoce fala portugues\b",
        r"\bvoce pode falar portugues\b",
        r"\bpode falar portugues\b",
        r"\bpode usar portugues\b",
        r"\bpode usar o portugues\b",
        r"\bpode misturar portugues\b",
        r"\bmistura portugues\b",
        r"\bmisture portugues\b",
        r"\bquero portugues tambem\b",
        r"\bquero usar portugues tambem\b",
        r"\bquero portugues junto\b",
        r"\bportugues junto\b",
        r"\bvolta pro portugues\b",
        r"\bvolta para o portugues\b",
        r"\bvolta ao portugues\b",
        r"\bagora pode portugues\b",
        r"\bagora pode falar portugues\b",
        r"\bportugues pode\b",

        # Inglês
        r"\bspeak portuguese too\b",
        r"\bspeak portuguese also\b",
        r"\buse portuguese too\b",
        r"\buse portuguese also\b",
        r"\bportuguese too\b",
        r"\bportuguese as well\b",
        r"\bmix portuguese\b",
        r"\badd portuguese\b",
    ]

    return any(
        re.search(padrao, texto)
        for padrao in padroes
    )


# ============================================================
# DETECTOR DE PEDIDO DE AJUDA
# ============================================================

def parece_pedido_de_ajuda(texto: str) -> bool:

    texto = normalizar_texto(texto)

    padroes = [

        r"\bcomo fala\b",
        r"\bcomo eu falo\b",
        r"\bcomo dizer\b",
        r"\bcomo eu digo\b",
        r"\bcomo se fala\b",
        r"\bcomo posso dizer\b",
        r"\bcomo posso falar\b",
        r"\bqual a palavra\b",
        r"\bqual palavra\b",
        r"\bo que significa\b",
        r"\boq significa\b",
        r"\bnao sei falar\b",
        r"\bnao sei dizer\b",
        r"\bnao sei como dizer\b",
        r"\bcomo fala isso em ingles\b",
        r"\bcomo fala isso em ingles\b",
        r"\bcomo fala isso\b",
    ]

    return any(
        re.search(padrao, texto)
        for padrao in padroes
    )


# ============================================================
# ATUALIZA ESTADO DA CONVERSA
# ============================================================

def atualizar_estado_conversa(user_input: str):
    """
    Retorna:

    - modo atual
    - se o turno atual deve receber suporte bilíngue
    """

    # --------------------------------------------------------
    # Primeiro: pedido explícito de português/bilíngue
    # --------------------------------------------------------

    if usuario_pediu_bilingue(user_input):

        st.session_state.conversation_mode = "bilingual"

        return "bilingual"

    # --------------------------------------------------------
    # Segundo: pedido explícito de inglês
    # --------------------------------------------------------

    if usuario_pediu_ingles(user_input):

        st.session_state.conversation_mode = "english_only"

        return "english_only"

    # --------------------------------------------------------
    # Terceiro: pedido de ajuda
    #
    # Mesmo no English Only, uma pergunta do tipo:
    #
    # "Como fala X?"
    #
    # recebe suporte bilíngue naquele turno.
    # --------------------------------------------------------

    if parece_pedido_de_ajuda(user_input):

        return "bilingual_once"

    # --------------------------------------------------------
    # Nenhum comando especial.
    # --------------------------------------------------------

    return st.session_state.conversation_mode


# ============================================================
# ESTADO
# ============================================================

def resetar_conversa():

    st.session_state.messages = []

    st.session_state.audio_pendente = None

    st.session_state.turno = 0

    st.session_state.ultimo_audio_processado = None

    st.session_state.conversation_mode = DEFAULT_MODE


# ============================================================
# WHISPER
# ============================================================

@st.cache_resource
def load_whisper():

    return WhisperModel(
        WHISPER_MODEL_SIZE,
        device="cpu",
        compute_type="int8",
        cpu_threads=6
    )


model = load_whisper()


# ============================================================
# TTS
# ============================================================

async def gerar_audio_completo(
    texto: str,
    voz: str
) -> bytes:

    comunicador = edge_tts.Communicate(
        texto,
        voz
    )

    buffer = io.BytesIO()

    async for chunk in comunicador.stream():

        if chunk["type"] == "audio":
            buffer.write(chunk["data"])

    return buffer.getvalue()


# ============================================================
# HISTÓRICO
# ============================================================

def obter_historico():

    return st.session_state.messages[
        -MAX_HISTORY_MESSAGES:
    ]


# ============================================================
# PREPARAÇÃO DO SYSTEM PROMPT
# ============================================================

def criar_system_prompt(
    idioma_prompt: str,
    modo: str
) -> str:

    base = SYSTEM_PROMPT

    base += "\n\n"
    base += "==================================================\n"
    base += "CURRENT TARGET LANGUAGE\n"
    base += "==================================================\n"
    base += idioma_prompt

    base += "\n\n"
    base += "==================================================\n"
    base += "CURRENT CONVERSATION MODE\n"
    base += "==================================================\n"

    if modo == "english_only":

        base += """
ENGLISH ONLY.

The user explicitly wants English-only conversation.

Respond entirely in the target language.

DO NOT use Brazilian Portuguese.

DO NOT translate into Portuguese.

DO NOT add Portuguese explanations.
"""

    elif modo == "bilingual_once":

        base += """
BILINGUAL SUPPORT FOR THIS TURN.

The user appears to be asking for help expressing something.

Use the target language as the main language,
but use Brazilian Portuguese naturally to explain the requested expression.

After answering, continue naturally.
"""

    else:

        base += """
BILINGUAL SUPPORT.

Use the target language as the main language.

Naturally mix Brazilian Portuguese into the response
as support.

Do not translate everything.
"""

    return base


# ============================================================
# CHAMADA AO OLLAMA
# ============================================================

def gerar_resposta_llm(
    user_messages,
    idioma_prompt,
    modo
):

    system_prompt = criar_system_prompt(
        idioma_prompt,
        modo
    )

    mensagens = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    mensagens.extend(
        obter_historico()
    )

    inicio = time.perf_counter()

    resposta = ollama.chat(
        model=MODEL_NAME,
        messages=mensagens,
        stream=False,
        options=LLM_OPTIONS,
        keep_alive="5m",
    )

    tempo = time.perf_counter() - inicio

    texto = (
        resposta["message"]["content"]
        .strip()
    )

    return texto, tempo


# ============================================================
# VALIDAÇÃO DE PORTUGUÊS
# ============================================================

PALAVRAS_PORTUGUES = {
    "eu",
    "você",
    "voce",
    "meu",
    "minha",
    "isso",
    "essa",
    "esse",
    "aqui",
    "agora",
    "hoje",
    "amanhã",
    "amanha",
    "bom",
    "boa",
    "dia",
    "noite",
    "sim",
    "não",
    "nao",
    "mas",
    "porque",
    "como",
    "que",
    "para",
    "por",
    "com",
    "sem",
    "uma",
    "um",
    "está",
    "esta",
    "estou",
    "são",
    "sao",
    "foi",
    "ser",
    "ficou",
    "ficar",
    "pode",
    "vamos",
    "bora",
    "legal",
    "natural",
    "frase",
    "palavra",
    "forma",
    "jeito",
    "bem",
    "mais",
    "menos",
    "também",
    "tambem",
    "depois",
    "antes",
    "quer",
    "quero",
    "precisa",
    "preciso",
    "fala",
    "fale",
    "dizer",
    "ingles",
    "inglês",
}


def contem_portugues(texto: str) -> bool:

    texto = normalizar_texto(texto)

    palavras = set(
        re.findall(
            r"[a-z]+",
            texto
        )
    )

    encontradas = palavras.intersection(
        {
            normalizar_texto(palavra)
            for palavra in PALAVRAS_PORTUGUES
        }
    )

    return len(encontradas) >= 1


# ============================================================
# GERAÇÃO ROBUSTA
# ============================================================

def gerar_resposta(
    user_input: str,
    idioma_prompt: str
):

    # --------------------------------------------------------
    # Determina o comportamento DESSE turno.
    # --------------------------------------------------------

    modo_turno = atualizar_estado_conversa(
        user_input
    )

    # --------------------------------------------------------
    # Primeira geração
    # --------------------------------------------------------

    resposta, tempo = gerar_resposta_llm(
        st.session_state.messages,
        idioma_prompt,
        modo_turno
    )

    # --------------------------------------------------------
    # English Only:
    #
    # não tentar inserir português depois.
    # --------------------------------------------------------

    if modo_turno == "english_only":

        return resposta, tempo, modo_turno

    # --------------------------------------------------------
    # Pedido pontual de ajuda:
    #
    # não precisa validar português.
    # --------------------------------------------------------

    if modo_turno == "bilingual_once":

        return resposta, tempo, modo_turno

    # --------------------------------------------------------
    # Bilingual persistente:
    #
    # se já veio PT + idioma alvo, aceita.
    # --------------------------------------------------------

    if contem_portugues(resposta):

        return resposta, tempo, modo_turno

    # --------------------------------------------------------
    # Fallback:
    #
    # só fazemos segunda chamada se realmente necessário.
    # --------------------------------------------------------

    system_retry = criar_system_prompt(
        idioma_prompt,
        "bilingual"
    )

    system_retry += """

IMPORTANT CORRECTION.

Your previous response did not contain Brazilian Portuguese.

Regenerate the response.

Use the target language as the main language
and naturally include a short Brazilian Portuguese phrase.

Keep the response short.

Do not explain this correction.
"""

    mensagens_retry = [
        {
            "role": "system",
            "content": system_retry
        }
    ]

    mensagens_retry.extend(
        obter_historico()
    )

    inicio_retry = time.perf_counter()

    resposta_retry = ollama.chat(
        model=MODEL_NAME,
        messages=mensagens_retry,
        stream=False,
        options=LLM_OPTIONS,
        keep_alive="5m",
    )

    tempo_retry = (
        time.perf_counter()
        - inicio_retry
    )

    resposta_final = (
        resposta_retry["message"]["content"]
        .strip()
    )

    return (
        resposta_final,
        tempo + tempo_retry,
        modo_turno
    )


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    :root {
        --bg: #09090b;
        --accent: #8b5cf6;
    }

    .stApp {
        background: var(--bg);
        color: #e4e4e7;
    }

    .msg-ai {
        background: #18181b;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #27272a;
        margin-bottom: 10px;
    }

    .msg-user {
        background: #2e1065;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# INICIALIZAÇÃO
# ============================================================

if "messages" not in st.session_state:
    resetar_conversa()

if "audio_pendente" not in st.session_state:
    st.session_state.audio_pendente = None

if "turno" not in st.session_state:
    st.session_state.turno = 0

if "ultimo_audio_processado" not in st.session_state:
    st.session_state.ultimo_audio_processado = None

if "conversation_mode" not in st.session_state:
    st.session_state.conversation_mode = DEFAULT_MODE


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("AI Language Tutor")

    st.divider()

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    lang_key = st.selectbox(
        "Practice Language",
        list(IDIOMAS.keys())
    )

    lang_info = IDIOMAS[
        lang_key
    ]

    # --------------------------------------------------------
    # VOICE
    # --------------------------------------------------------

    voz_nome = st.selectbox(
        "Voice",
        list(VOZES.keys()),
        index=0
    )

    voz_id = VOZES[
        voz_nome
    ]

    # --------------------------------------------------------
    # MODE
    # --------------------------------------------------------

    st.subheader(
        "Conversation Mode"
    )

    modo_label = st.radio(
        "Mode",
        [
            "🇺🇸 English Only",
            "🇺🇸🇧🇷 Bilingual Support",
        ],
        index=(
            0
            if st.session_state.conversation_mode
            == "english_only"
            else 1
        ),
    )

    novo_modo = (
        "english_only"
        if modo_label == "🇺🇸 English Only"
        else "bilingual"
    )

    if (
        novo_modo
        != st.session_state.conversation_mode
    ):

        st.session_state.conversation_mode = (
            novo_modo
        )

    st.divider()

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if (
        st.session_state.conversation_mode
        == "english_only"
    ):

        st.success(
            "English Only"
        )

    else:

        st.info(
            "Bilingual Support"
        )

    st.caption(
        f"LLM: {MODEL_NAME}"
    )

    st.caption(
        f"Whisper: {WHISPER_MODEL_SIZE}"
    )

    # --------------------------------------------------------
    # NOVA CONVERSA
    # --------------------------------------------------------

    if st.button(
        "New Conversation",
        use_container_width=True
    ):

        resetar_conversa()

        st.rerun()


# ============================================================
# HISTÓRICO
# ============================================================

for msg in st.session_state.messages:

    with st.chat_message(
        msg["role"]
    ):

        st.markdown(
            msg["content"]
        )


# ============================================================
# INPUT
# ============================================================

audio_file = st.audio_input(
    "Record",
    key=f"audio_input_{st.session_state.turno}"
)

prompt = st.chat_input(
    "Say something..."
)

user_input = None


# ============================================================
# ÁUDIO / WHISPER
# ============================================================

if audio_file is not None:

    audio_bytes = (
        audio_file.getvalue()
    )

    if (
        audio_bytes
        != st.session_state.ultimo_audio_processado
    ):

        st.session_state.ultimo_audio_processado = (
            audio_bytes
        )

        with st.spinner(
            "Transcribing..."
        ):

            segmentos, _ = model.transcribe(
                audio_file,
                beam_size=5,
                vad_filter=True
            )

            user_input = " ".join(
                segmento.text
                for segmento in segmentos
            ).strip()


# ============================================================
# TEXTO
# ============================================================

if prompt:

    user_input = prompt.strip()


# ============================================================
# PROCESSAMENTO
# ============================================================

if user_input:

    # --------------------------------------------------------
    # Salva usuário
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    # --------------------------------------------------------
    # Gera resposta
    # --------------------------------------------------------

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "Thinking..."
        ):

            inicio_total = time.perf_counter()

            full_text, tempo_llm, modo_turno = gerar_resposta(
                user_input,
                lang_info["prompt"]
            )

            tempo_total_llm = (
                time.perf_counter()
                - inicio_total
            )

        # ----------------------------------------------------
        # TEXTO
        # ----------------------------------------------------

        st.markdown(
            full_text
        )

        # ----------------------------------------------------
        # DEBUG / TEMPOS
        # ----------------------------------------------------

        st.caption(
            f"LLM: {tempo_total_llm:.2f}s • Mode: {modo_turno}"
        )

        # ----------------------------------------------------
        # HISTÓRICO
        # ----------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": full_text
            }
        )

        # ----------------------------------------------------
        # TTS
        # ----------------------------------------------------

        try:

            with st.spinner(
                "Generating voice..."
            ):

                inicio_tts = time.perf_counter()

                audio_bytes = asyncio.run(
                    gerar_audio_completo(
                        full_text,
                        voz_id
                    )
                )

                tempo_tts = (
                    time.perf_counter()
                    - inicio_tts
                )

            st.session_state.audio_pendente = (
                audio_bytes
            )

            st.caption(
                f"TTS: {tempo_tts:.2f}s"
            )

        except Exception as e:

            st.error(
                f"TTS Error: {e}"
            )

        # ----------------------------------------------------
        # Próximo turno
        # ----------------------------------------------------

        st.session_state.turno += 1

        st.rerun()


# ============================================================
# ÁUDIO
# ============================================================

if st.session_state.audio_pendente:

    st.audio(
        st.session_state.audio_pendente,
        format="audio/mp3",
        autoplay=True
    )

    st.session_state.audio_pendente = None