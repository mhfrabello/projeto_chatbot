# components/sidebar.py
"""
Barra lateral: indicadores da base de conhecimento e ações (limpar
conversa, recarregar base).
"""
import streamlit as st


def render_sidebar(num_entradas: int, num_chunks: int, on_reload, on_clear):
    with st.sidebar:
        st.markdown("##### Base de conhecimento")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f"""<div class="metric-card">
                    <div class="valor">{num_entradas}</div>
                    <div class="rotulo">Situações</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"""<div class="metric-card">
                    <div class="valor">{num_chunks}</div>
                    <div class="rotulo">Indexadas</div>
                </div>""",
                unsafe_allow_html=True,
            )

        if st.button("🔄 Recarregar base de conhecimento", use_container_width=True):
            on_reload()

        st.divider()

        st.markdown("##### Conversa")
        if st.button("🗑️ Limpar conversa", use_container_width=True):
            on_clear()

        st.divider()
        st.caption(
            "As URLs de chamados usadas neste assistente são fictícias, "
            "para fins de demonstração."
        )
