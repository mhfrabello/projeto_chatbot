# components/chat_ui.py
"""
Componentes visuais da área principal de chat: header institucional e
tela inicial com exemplos clicáveis.
"""
import streamlit as st

EXEMPLOS_INICIAIS = [
    ("💻", "Meu computador não liga"),
    ("📥", "Preciso instalar um programa"),
    ("🔑", "Esqueci minha senha"),
    ("🚪", "Estou sem acesso a um sistema"),
    ("🖥️", "Meu monitor está com problema"),
    ("✅", "Preciso solicitar acesso"),
]


def render_header(app_title: str):
    st.markdown(
        f"""
        <div class="app-header">
            <div class="icone">🎫</div>
            <div class="titulos">
                <h1>{app_title}</h1>
                <p>Orientação para abertura de chamados e resolução de problemas de TI</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> str | None:
    """
    Mostra a tela inicial com exemplos clicáveis. Retorna o texto do
    exemplo clicado (para ser tratado como se fosse digitado pelo
    colaborador), ou None se nada foi clicado ainda.
    """
    st.markdown(
        """
        <div class="tela-inicial">
            <h2>Olá! 👋 Sou o Assistente de TI.</h2>
            <p>
                Descreva o problema que você está enfrentando e eu vou orientar
                como resolver sozinho, qual chamado abrir, qual categoria usar
                e onde abrir — direto ao ponto.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    st.caption("Ou escolha um exemplo:")

    pergunta_clicada = None
    colunas = st.columns(2)
    for indice, (emoji, texto) in enumerate(EXEMPLOS_INICIAIS):
        coluna = colunas[indice % 2]
        with coluna:
            if st.button(f"{emoji}  {texto}", key=f"exemplo_{indice}"):
                pergunta_clicada = texto

    return pergunta_clicada
