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
        st.warning("Sem dados.")
        return

    opcoes = mes_ano()
    mes_atual = datetime.now().strftime("%m/%Y")
    mes_sel = st.segmented_control("Meses", options=opcoes, default=mes_atual, selection_mode="single",
                                   label_visibility="collapsed") or mes_atual

    df_chart = df.copy()
    # CORREÇÃO AQUI: format='mixed'
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
        st.info("Sem dados para este mês.")