import streamlit as st
import pandas as pd
import plotly.express as px
from services.calendar_service import mes_ano
from datetime import datetime


def dashboard_page(df):
    st.markdown(
        "<style>div[data-testid='stSegmentedControl'] button {min-height: 55px; min-width: 80px; font-weight: bold;}</style>",
        unsafe_allow_html=True)
    st.header("📈 Dashboard Analítico")

    if df.empty:
        st.warning("Sem dados para gerar o Dashboard.")
        return

    # --- CÁLCULOS DE RESERVA DE EMERGÊNCIA (H4.3) ---
    df_reserva = df.copy()
    df_reserva['data_vencimento'] = pd.to_datetime(df_reserva['data_vencimento'], format='mixed')

    # 1. Saldo Total Disponível (Histórico)
    receitas_totais = df_reserva[df_reserva['tipo'] == "Receita"]['valor'].sum()
    despesas_totais = df_reserva[df_reserva['tipo'] == "Despesa"]['valor'].sum()
    saldo_acumulado = receitas_totais - despesas_totais

    # 2. Custo Mensal Médio (Baseado nos meses que têm despesas)
    gastos_por_mes = df_reserva[df_reserva['tipo'] == "Despesa"].groupby(
        df_reserva['data_vencimento'].dt.to_period('M'))['valor'].sum()

    custo_medio = gastos_por_mes.mean() if not gastos_por_mes.empty else 0
    meta_reserva = custo_medio * 6  # Padrão: 6 meses de sobrevivência

    # 3. UI da Reserva
    with st.container(border=True):
        st.subheader("🛡️ Saúde Financeira: Reserva de Emergência")
        c1, c2, c3 = st.columns(3)

        c1.metric("Custo Médio Mensal", f"R$ {custo_medio:,.2f}")
        c2.metric("Meta de Reserva (6 meses)", f"R$ {meta_reserva:,.2f}")

        # Progresso da Reserva
        if meta_reserva > 0:
            progresso = min(saldo_acumulado / meta_reserva, 1.0) if saldo_acumulado > 0 else 0
            cor_progresso = "green" if progresso >= 1 else "orange" if progresso > 0.5 else "red"

            c3.metric("Saldo Atual vs Meta", f"{progresso * 100:.1f}%")
            st.progress(progresso)

            if progresso >= 1:
                st.success("🎯 Parabéns! Sua reserva de emergência está completa.")
            elif progresso > 0:
                meses_cobertos = saldo_acumulado / custo_medio if custo_medio > 0 else 0
                st.info(f"Seu saldo atual cobre aproximadamente **{meses_cobertos:.1f} meses** de despesas.")
        else:
            st.info("Lance despesas para calcular sua meta de reserva.")

    st.write("---")

    # --- FILTRO POR MÊS (SEU CÓDIGO ORIGINAL) ---
    opcoes = mes_ano()
    mes_atual = datetime.now().strftime("%m/%Y")
    mes_sel = st.segmented_control("Meses", options=opcoes, default=mes_atual, selection_mode="single",
                                   label_visibility="collapsed") or mes_atual

    df_chart = df.copy()
    df_chart['data_vencimento'] = pd.to_datetime(df_chart['data_vencimento'], format='mixed')

    mes_f, ano_f = map(int, mes_sel.split('/'))
    mask = (df_chart['data_vencimento'].dt.month == mes_f) & (df_chart['data_vencimento'].dt.year == ano_f)
    df_filtrado = df_chart[mask]

    if not df_filtrado.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.write("### Despesas por Categoria")
            fig_pizza = px.pie(df_filtrado[df_filtrado['tipo'] == 'Despesa'], values='valor', names='categoria',
                               hole=0.4)
            st.plotly_chart(fig_pizza, use_container_width=True)
        with col2:
            st.write("### Evolução Diária")
            df_evol = df_filtrado.groupby(['data_vencimento', 'tipo'])['valor'].sum().reset_index()
            fig_line = px.line(df_evol, x='data_vencimento', y='valor', color='tipo', markers=True)
            st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info(f"Sem dados detalhados para {mes_sel}.")