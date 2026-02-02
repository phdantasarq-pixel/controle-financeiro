import streamlit as st
from domain.analise import (
    calcular_pareto_categorias,
    gerar_grafico_pareto,
    calcular_performance_pagamentos,
    gerar_grafico_performance
)


def analise_categorias_page(df):
    st.header("🎯 Inteligência Financeira")
    st.write("Análise de impacto (Pareto) e status de execução (Performance).")

    # --- SEÇÃO 1: ANÁLISE DE PARETO (SUBIU!) ---
    st.subheader("📊 Onde está o seu dinheiro?")
    df_pareto = calcular_pareto_categorias(df)

    if df_pareto is not None:
        # KPI dos Vilões (Categorias que somam até ~85% do gasto)
        viloes = df_pareto[df_pareto['acumulado'] <= 85]['categoria'].tolist()

        c1, c2 = st.columns([2, 1])

        with c1:
            fig_pareto = gerar_grafico_pareto(df_pareto)
            st.plotly_chart(fig_pareto, use_container_width=True)

        with c2:
            st.markdown("### 🕵️ Os Vilões")
            for i, cat in enumerate(viloes):
                st.error(f"{i + 1}º - {cat}")
            st.info("💡 Focar em reduzir estes itens trará o maior impacto financeiro.")

        # Tabela Detalhada
        with st.expander("🔍 Ver Detalhes das Categorias"):
            st.table(df_pareto.style.format({
                "valor": "R$ {:.2f}",
                "percentual": "{:.1f}%",
                "acumulado": "{:.1f}%"
            }))
    else:
        st.info("Lance algumas despesas para visualizar a análise de Pareto.")

    st.divider()

    # --- SEÇÃO 2: PERFORMANCE DE PAGAMENTOS (Donut Chart) ---
    st.subheader("🕒 Status de Pagamentos (Despesas)")

    df_status = calcular_performance_pagamentos(df)
    if df_status is not None:
        col_perf, col_info = st.columns([1, 1])

        with col_perf:
            fig_perf = gerar_grafico_performance(df_status)
            st.plotly_chart(fig_perf, use_container_width=True)

        with col_info:
            # Cálculo rápido para KPI
            total_pendente = df_status[df_status['status'] == 'Pendente']['valor'].sum()
            st.metric("Total Pendente", f"R$ {total_pendente:,.2f}", delta_color="inverse")
            st.info("Otimize seu fluxo de caixa garantindo que as pendências não acumulem juros.")