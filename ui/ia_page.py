import streamlit as st
from services.ia_service import IAService
from services.database import Database
import pandas as pd
from datetime import datetime
from ui.layout import page_header, section, card_container


def ia_page(df_lancamentos):
    # O cabeçalho agora usa o padrão do sistema
    st.header("🤖 Consultoria PlanejAI")
    st.caption("Inteligência Artificial analisando seus dados e fluxos de caixa em tempo real.")

    # --- 1. CÁLCULO DE INDICADORES (Mantido seu cálculo original) ---
    saldo_atual_contas = Database.obter_total_saldos_real()
    df_p = df_lancamentos.copy()
    df_p['data_vencimento'] = pd.to_datetime(df_p['data_vencimento'], errors='coerce')
    hoje = datetime.now()

    df_atual = df_p[(df_p['data_vencimento'].dt.month == hoje.month) &
                    (df_p['data_vencimento'].dt.year == hoje.year)].copy()

    rec_pend_atual = df_atual[(df_atual['tipo'] == "Receita") & (df_atual['status'] != "Concluído")]['valor'].sum()
    desp_pend_atual = df_atual[(df_atual['tipo'] == "Despesa") & (df_atual['status'] != "Concluído")]['valor'].sum()

    saldo_fechamento_atual = saldo_atual_contas + rec_pend_atual - desp_pend_atual
    balanco_mensal = df_atual[df_atual['tipo'] == "Receita"]['valor'].sum() - df_atual[df_atual['tipo'] == "Despesa"][
        'valor'].sum()

    indicadores_ia = {
        "saldo_contas": saldo_atual_contas,
        "saldo_projetado": saldo_fechamento_atual,
        "balanco": balanco_mensal
    }

    # 2. CONTEXTO
    df_saldos = Database.carregar_saldos()
    contexto_completo = {"lancamentos": df_lancamentos, "saldos": df_saldos}

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 3. CONTAINER DE INSIGHTS (Agora com borda estilizada pelo tema)
    with st.container():
        st.subheader("🎯 Insight do Mês")
        if st.button("✨ Gerar Análise de Fluxo", use_container_width=True):
            with st.spinner("Calculando impacto nas reservas..."):
                ai = IAService()
                insight = ai.gerar_insight(contexto_completo, hoje.strftime("%m/%Y"), indicadores=indicadores_ia)
                st.info(insight)  # st.info costuma respeitar melhor o tema claro

    st.markdown("---")

    # 4. ÁREA DO CHAT (Com correção de contraste)
    st.subheader("💬 Chat Direto com PlanejAI")

    # Exibe histórico
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input do Chat
    if prompt := st.chat_input("Ex: Vou fechar o mês no azul?"):
        # Adiciona e exibe mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Gera e exibe resposta da IA
        with st.chat_message("assistant"):
            with st.spinner("Analisando projeções..."):
                ai = IAService()
                resposta = ai.chat(prompt, contexto_completo, st.session_state.messages, indicadores=indicadores_ia)
                st.markdown(resposta)
                st.session_state.messages.append({"role": "assistant", "content": resposta})

        # Rerun após processar tudo para limpar o input
        st.rerun()