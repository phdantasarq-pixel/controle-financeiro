import streamlit as st
from services.ia_service import IAService
from services.database import Database
import pandas as pd


def ia_page(df_lancamentos):
    st.header("🤖 Consultoria PlanejAI")
    st.caption("Inteligência Artificial analisando seus dados e saldos.")

    # 1. BUSCA DE CONTEXTO
    df_saldos = Database.carregar_saldos()
    contexto_completo = {
        "lancamentos": df_lancamentos,
        "saldos": df_saldos
    }

    # 2. INICIALIZAÇÃO DO HISTÓRICO (Vital para não resetar)
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 3. CONTAINER DE INSIGHTS (O botão que você já tinha)
    with st.container(border=True):
        if st.button("✨ Gerar Insight Estratégico", use_container_width=True):
            with st.spinner("Analisando..."):
                ai = IAService()
                insight = ai.gerar_insight(contexto_completo, "01/2026")
                st.markdown(insight)

    st.write("---")

    # 4. ÁREA DO CHAT INTERATIVO
    st.subheader("💬 Chat Direto com PlanejAI")

    # Exibe as mensagens que já estão no histórico
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Captura a nova pergunta
    if prompt := st.chat_input("Ex: Como sair das dívidas com meu saldo atual?"):
        # Adiciona mensagem do usuário ao estado
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Exibe na tela imediatamente
        with st.chat_message("user"):
            st.markdown(prompt)

        # Gera a resposta da IA
        with st.chat_message("assistant"):
            with st.spinner("O PlanejAI está pensando..."):
                ai = IAService()
                # Chama o método chat (que criamos no passo anterior)
                resposta = ai.chat(prompt, contexto_completo, st.session_state.messages)
                st.markdown(resposta)

        # Salva a resposta da IA para não sumir no próximo refresh
        st.session_state.messages.append({"role": "assistant", "content": resposta})

        # Força o Streamlit a atualizar para manter o scroll do chat
        st.rerun()