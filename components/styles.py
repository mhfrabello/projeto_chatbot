# components/styles.py
"""
CSS customizado para dar ao assistente uma aparência de portal corporativo
interno — não de protótipo padrão do Streamlit.

Tema escuro fixo (não depende da preferência de sistema do usuário). O
Streamlit aplica automaticamente dark/light baseado no SO/navegador, o que
antes causava mistura de fundo claro com fundo escuro em containers
diferentes. Fixar tudo como dark aqui, reforçado por .streamlit/config.toml,
elimina essa inconsistência.
"""

CUSTOM_CSS = """
<style>
:root {
    --cor-primaria: #3B82C4;
    --cor-primaria-clara: #5B9FDB;
    --cor-fundo: #12161C;
    --cor-fundo-card: #1B212B;
    --cor-fundo-card-hover: #232A36;
    --cor-texto: #ECEFF3;
    --cor-texto-suave: #9AA4B2;
    --cor-borda: #2C3542;
    --cor-sucesso: #4ADE9C;
    --cor-sucesso-fundo: #16332A;
    --cor-acao: #E0A25E;
    --cor-acao-fundo: #3A2C18;
    --cor-erro: #F0796A;
    --cor-erro-fundo: #3A1E1B;
}

/* ============================================================
   1) FUNDO E TEXTO — todos os containers estruturais do Streamlit
   ============================================================ */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stBottomBlockContainer"],
[data-testid="stBottom"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
section[data-testid="stSidebar"],
[data-testid="stSidebarContent"] {
    background-color: var(--cor-fundo) !important;
    color: var(--cor-texto) !important;
}

[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* Input de chat na parte inferior */
[data-testid="stChatInput"] {
    background-color: var(--cor-fundo-card) !important;
    border: 1px solid var(--cor-borda) !important;
}
[data-testid="stChatInput"] textarea {
    background-color: var(--cor-fundo-card) !important;
    color: var(--cor-texto) !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: var(--cor-texto-suave) !important;
    opacity: 1;
}
[data-testid="stChatInputSubmitButton"] {
    background-color: var(--cor-primaria) !important;
}
[data-testid="stChatInputSubmitButton"] svg {
    fill: #FFFFFF !important;
}

/* Todo texto genérico segue a cor clara, em qualquer container */
.stApp p, .stApp span, .stApp li, .stApp label,
.stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp div[data-testid="stMarkdownContainer"],
.stApp div[data-testid="stCaptionContainer"] {
    color: var(--cor-texto) !important;
}
.stApp div[data-testid="stCaptionContainer"] {
    color: var(--cor-texto-suave) !important;
}

hr, [data-testid="stSidebar"] hr {
    border-color: var(--cor-borda) !important;
}

/* Fonte do sistema — combina com o ambiente Windows do usuário */
html, body, [class*="css"] {
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
}

/* Esconde o menu hamburguer/rodapé padrão do Streamlit */
#MainMenu, footer {visibility: hidden;}

/* ============================================================
   2) HEADER INSTITUCIONAL
   ============================================================ */
.app-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 18px 24px;
    background: linear-gradient(135deg, #1E3A54, #16283A);
    border: 1px solid var(--cor-borda);
    border-radius: 10px;
    margin-bottom: 28px;
}
.app-header .icone {
    width: 42px;
    height: 42px;
    border-radius: 8px;
    background: rgba(255,255,255,0.08);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    flex-shrink: 0;
}
.app-header .titulos h1 {
    color: #FFFFFF !important;
    font-size: 19px;
    font-weight: 600;
    margin: 0;
    line-height: 1.3;
}
.app-header .titulos p {
    color: rgba(255,255,255,0.65) !important;
    font-size: 13.5px;
    margin: 2px 0 0 0;
}

/* ============================================================
   3) TELA INICIAL (sem conversa ainda)
   ============================================================ */
.tela-inicial {
    text-align: left;
    padding: 8px 4px 4px 4px;
}
.tela-inicial h2 {
    font-size: 22px;
    color: var(--cor-texto) !important;
    margin-bottom: 6px;
}
.tela-inicial p {
    color: var(--cor-texto-suave) !important;
    font-size: 15px;
    line-height: 1.6;
    max-width: 560px;
}

/* ============================================================
   4) BOTÕES (exemplos clicáveis + ações da sidebar)
   ============================================================ */
div[data-testid="stButton"] > button {
    width: 100%;
    text-align: left;
    background: var(--cor-fundo-card) !important;
    border: 1px solid var(--cor-borda) !important;
    border-radius: 8px;
    padding: 12px 14px;
    color: var(--cor-texto) !important;
    font-size: 14px;
    font-weight: 400;
    transition: border-color 0.15s ease, background 0.15s ease;
}
div[data-testid="stButton"] > button p {
    color: var(--cor-texto) !important;
}
div[data-testid="stButton"] > button:hover {
    border-color: var(--cor-primaria-clara) !important;
    background: var(--cor-fundo-card-hover) !important;
    color: var(--cor-primaria-clara) !important;
}
div[data-testid="stButton"] > button:hover p {
    color: var(--cor-primaria-clara) !important;
}
div[data-testid="stButton"] > button:focus {
    box-shadow: 0 0 0 2px var(--cor-primaria-clara);
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
    font-size: 13px;
    padding: 8px 12px;
}

/* ============================================================
   5) CARTÕES DE MÉTRICA NA SIDEBAR
   ============================================================ */
.metric-card {
    background: var(--cor-fundo-card) !important;
    border: 1px solid var(--cor-borda);
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 10px;
}
.metric-card .valor {
    font-size: 22px;
    font-weight: 700;
    color: var(--cor-primaria-clara) !important;
    line-height: 1.2;
}
.metric-card .rotulo {
    font-size: 12.5px;
    color: var(--cor-texto-suave) !important;
    margin-top: 2px;
}

/* ============================================================
   6) AVISOS (erro / base vazia)
   ============================================================ */
.aviso-erro {
    background: var(--cor-erro-fundo) !important;
    border-left: 3px solid var(--cor-erro);
    border-radius: 6px;
    padding: 14px 16px;
    color: var(--cor-texto) !important;
    font-size: 14px;
    line-height: 1.5;
}
.aviso-vazio {
    background: var(--cor-acao-fundo) !important;
    border-left: 3px solid var(--cor-acao);
    border-radius: 6px;
    padding: 14px 16px;
    color: var(--cor-texto) !important;
    font-size: 14px;
    line-height: 1.5;
}

/* ============================================================
   7) BOLHAS DE CHAT
   ============================================================ */
div[data-testid="stChatMessage"] {
    background: var(--cor-fundo-card) !important;
    border-radius: 10px;
    padding: 10px 14px;
    border: 1px solid var(--cor-borda);
}

/* Avatares do chat — remove fundo claro padrão do Streamlit */
[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessageAvatarAssistant"] {
    background-color: var(--cor-primaria) !important;
}

/* Links de chamado dentro das respostas — destaque visual como "botão" */
div[data-testid="stChatMessageContent"] a {
    display: inline-block;
    background: var(--cor-acao-fundo) !important;
    color: var(--cor-acao) !important;
    border: 1px solid var(--cor-acao);
    border-radius: 6px;
    padding: 6px 14px;
    text-decoration: none;
    font-weight: 600;
    font-size: 13.5px;
    margin: 4px 0;
}
div[data-testid="stChatMessageContent"] a:hover {
    background: var(--cor-acao) !important;
    color: #1A1D23 !important;
}

/* Código inline/blocos, caso apareçam nas respostas */
.stApp code {
    background: var(--cor-fundo-card-hover) !important;
    color: var(--cor-acao) !important;
    border: 1px solid var(--cor-borda);
}
</style>
"""
