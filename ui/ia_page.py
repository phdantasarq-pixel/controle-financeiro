import streamlit as st
from services.ia_service import IAService
from services.database import Database
import pandas as pd
from datetime import datetime
from ui.layout import page_header, section, card_container



def ia_page(df_lancamentos):
    st.header("🤖 Consultoria PlanejAI")
    st.caption("Inteligência Artificial analisando seus dados e fluxos de caixa em tempo real.")

    # --- 1. CÁLCULO DE INDICADORES PARA A IA [H8.1] ---
    # Buscamos o saldo real hoje
    saldo_atual_contas = Database.obter_total_saldos_real()

    # Processamos o saldo projetado (Fim do Mês Atual)
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

    # Dicionário de indicadores para precisão da IA
    indicadores_ia = {
        "saldo_contas": saldo_atual_contas,
        "saldo_projetado": saldo_fechamento_atual,
        "balanco": balanco_mensal
    }

    # 2. BUSCA DE CONTEXTO ADICIONAL
    df_saldos = Database.carregar_saldos()
    contexto_completo = {
        "lancamentos": df_lancamentos,
        "saldos": df_saldos
    }

    # 3. INICIALIZAÇÃO DO HISTÓRICO
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 4. CONTAINER DE INSIGHTS
    with st.container(border=True):
        st.subheader("🎯 Insight do Mês")
        if st.button("✨ Gerar Análise de Fluxo", use_container_width=True):
            with st.spinner("Calculando impacto nas reservas..."):
                ai = IAService()
                insight = ai.gerar_insight(contexto_completo, hoje.strftime("%m/%Y"), indicadores=indicadores_ia)
                st.markdown(insight)

    st.write("---")

    # 5. ÁREA DO CHAT INTERATIVO
    st.subheader("💬 Chat Direto com PlanejAI")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ex: Vou fechar o mês no azul?"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analisando projeções..."):
                ai = IAService()
                # O chat agora também recebe os indicadores calculados
                resposta = ai.chat(prompt, contexto_completo, st.session_state.messages, indicadores=indicadores_ia)
                st.markdown(resposta)

        st.session_state.messages.append({"role": "assistant", "content": resposta})
        st.rerun()