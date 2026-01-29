import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from ui.components import seletor_meses_inteligente
from services.database import Database


def dashboard_page(df):
    st.markdown(
        "<style>div[data-testid='stSegmentedControl'] button {min-height: 55px; min-width: 80px; font-weight: bold;}</style>",
        unsafe_allow_html=True)
    st.header("📈 Dashboard Analítico")

    if df.empty:
        st.warning("Sem dados para gerar o Dashboard.")
        return

    # --- CÁLCULOS DE RESERVA (H7.1) ---
    df_reserva = df.copy()
    df_reserva['data_vencimento'] = pd.to_datetime(df_reserva['data_vencimento'], errors='coerce')

    # 1. Busca saldos manuais
    df_saldos_manuais = Database.carregar_saldos()
    total_contas = df_saldos_manuais['valor'].sum() if not df_saldos_manuais.empty else 0

    # 2. Saldo do Extrato
    receitas_totais = df_reserva[df_reserva['tipo'] == "Receita"]['valor'].sum()
    despesas_totais = df_reserva[df_reserva['tipo'] == "Despesa"]['valor'].sum()
    saldo_extrato = receitas_totais - despesas_totais

    # 3. RESERVA TOTAL REAL (Impactada pelos saldos manuais)
    reserva_total_real = saldo_extrato + total_contas

    # 4. Meta baseada em Gastos
    gastos_por_mes = df_reserva[df_reserva['tipo'] == "Despesa"].groupby(
        df_reserva['data_vencimento'].dt.to_period('M'))['valor'].sum()
    custo_medio = gastos_por_mes.mean() if not gastos_por_mes.empty else 0
    meta_reserva = custo_medio * 6

    # --- UI DA RESERVA ---
    with st.container(border=True):
        st.subheader("🛡️ Saúde Financeira: Reserva de Emergência")
        c1, c2, c3 = st.columns(3)

        c1.metric("Custo Médio Mensal", f"R$ {custo_medio:,.2f}")
        c2.metric("Meta de Reserva (6 meses)", f"R$ {meta_reserva:,.2f}")

        if meta_reserva > 0:
            progresso = min(reserva_total_real / meta_reserva, 1.0) if reserva_total_real > 0 else 0
            c3.metric("Saldo Real p/ Reserva", f"R$ {reserva_total_real:,.2f}", delta=f"{progresso * 100:.1f}%")
            st.progress(progresso)

            if progresso >= 1:
                st.success("🎯 Parabéns! Sua reserva de emergência está completa.")
            else:
                meses_cobertos = reserva_total_real / custo_medio if custo_medio > 0 else 0
                st.info(f"Sua reserva atual cobre aproximadamente **{meses_cobertos:.1f} meses** de despesas.")

    st.write("---")

    # --- FILTRO E GRÁFICOS ---
    mes_sel = seletor_meses_inteligente(key_suffix="dash_analitico")
    mes_f, ano_f = map(int, mes_sel.split('/'))

    df_chart = df.copy()
    df_chart['data_vencimento'] = pd.to_datetime(df_chart['data_vencimento'], errors='coerce')
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