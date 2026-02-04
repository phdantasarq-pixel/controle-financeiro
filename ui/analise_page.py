import streamlit as st
import pandas as pd
from domain.analise import (
    calcular_pareto_categorias,
    gerar_grafico_pareto,
    calcular_performance_pagamentos,
    gerar_grafico_performance
)


def analise_categorias_page(df):
    st.header("🎯 Inteligência Financeira")
    st.write("Análise de eficiência, impacto de gastos e saúde circulatória.")

    if df.empty:
        st.warning("Sem dados suficientes para análise.")
        return

    # --- LÓGICA DE CAPACIDADE DE RESERVA ---
    receita_total = df[df['tipo'] == "Receita"]['valor'].sum()
    despesa_total = df[df['tipo'] == "Despesa"]['valor'].sum()
    sobra_liquida = receita_total - despesa_total
    capacidade_aporte = (sobra_liquida / receita_total) * 100 if receita_total > 0 else 0

    # --- SEÇÃO 1: POTENCIAL DE RESERVA ---
    with st.container(border=True):
        st.subheader("🛡️ Potencial de Reserva (Mensal)")
        c1, c2, c3 = st.columns(3)
        c1.metric("Sobra Líquida", f"R$ {sobra_liquida:,.2f}")
        c2.metric("Capacidade de Aporte", f"{capacidade_aporte:.1f}%")
        c3.metric("Eficiência de Gastos", f"{(despesa_total / receita_total * 100) if receita_total > 0 else 0:.1f}%",
                  delta_color="inverse")
        st.progress(max(0.0, min(capacidade_aporte / 100, 1.0)))

    st.divider()

    # --- SEÇÃO 2: STATUS DE PAGAMENTOS (CORRIGIDO) ---
    st.subheader("🕒 Saúde do Fluxo de Caixa")

    df_status = calcular_performance_pagamentos(df)

    if df_status is not None and not df_status.empty:
        # Normalizamos o status para minúsculo para garantir a contagem correta
        df_status['status_norm'] = df_status['status'].str.lower().str.strip()

        pago = df_status[df_status['status_norm'] == 'pago']['valor'].sum()
        pendente = df_status[df_status['status_norm'] == 'pendente']['valor'].sum()
        atrasado = df_status[df_status['status_norm'] == 'atrasado']['valor'].sum()

        total_despesas = pago + pendente + atrasado

        # Cards de Status
        col1, col2, col3 = st.columns(3)
        with col1:
            st.success(f"**Liquidado**\nR$ {pago:,.2f}")
            st.caption(f"{(pago / total_despesas * 100) if total_despesas > 0 else 0:.1f}% concluído")
        with col2:
            st.warning(f"**A Pagar**\nR$ {pendente:,.2f}")
            st.caption("Aguardando vencimento")
        with col3:
            st.error(f"**Em Atraso**\nR$ {atrasado:,.2f}")
            st.caption("Risco de juros e multas")

        # Barra de Execução Financeira (Ajuste de pesos para evitar erro de divisão por zero)
        st.write("**Progresso de Quitação Mensal:**")
        # Criamos pesos visuais: se o valor for 0, a coluna fica mínima (0.01)
        w_pago = max(pago, 0.01)
        w_pend = max(pendente, 0.01)
        w_atra = max(atrasado, 0.01)

        cols_barra = st.columns([w_pago, w_pend, w_atra])
        with cols_barra[0]:
            st.markdown(
                f'<div title="Pago: R$ {pago:.2f}" style="height:12px; background-color:#28a745; border-radius:5px;"></div>',
                unsafe_allow_html=True)
        with cols_barra[1]:
            st.markdown(
                f'<div title="Pendente: R$ {pendente:.2f}" style="height:12px; background-color:#ffc107; border-radius:5px;"></div>',
                unsafe_allow_html=True)
        with cols_barra[2]:
            st.markdown(
                f'<div title="Atrasado: R$ {atrasado:.2f}" style="height:12px; background-color:#dc3545; border-radius:5px;"></div>',
                unsafe_allow_html=True)

    # --- SEÇÃO 3: ANÁLISE DE PARETO ---
    st.subheader("📊 Onde está o seu dinheiro? (Pareto)")
    df_pareto = calcular_pareto_categorias(df)

    if df_pareto is not None and not df_pareto.empty:
        viloes = df_pareto[df_pareto['acumulado'] <= 85]['categoria'].tolist()
        c_graf, c_viloes = st.columns([2, 1])

        with c_graf:
            fig_pareto = gerar_grafico_pareto(df_pareto)
            st.plotly_chart(fig_pareto, use_container_width=True)

        with c_viloes:
            st.markdown("### 🕵️ Os Vilões")
            for i, cat in enumerate(viloes):
                st.error(f"{i + 1}º - {cat}")
            st.info("💡 Focar aqui libera margem para sua reserva.")