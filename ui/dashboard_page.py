import streamlit as st
import pandas as pd
import plotly.express as px
from services.calendar_service import mes_ano


def dashboard_page(df):
    st.header("📈 Dashboard Financeiro")

    if df.empty:
        st.warning("Nenhum dado disponível para análise.")
        return

    # --- FILTROS LATERAIS (Ou no topo) ---
    st.subheader("Filtros de Análise")
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        opcoes_mes = mes_ano()
        mes_sel = st.selectbox("Período:", opcoes_mes)
    with col_f2:
        natureza_sel = st.multiselect("Natureza:", options=["Fixo", "Variável"], default=["Fixo", "Variável"])
    with col_f3:
        tipo_sel = st.multiselect("Tipo:", options=["Receita", "Despesa"], default=["Receita", "Despesa"])

    # --- PROCESSAMENTO DOS DADOS FILTRADOS ---
    df_chart = df.copy()
    df_chart['data_vencimento'] = pd.to_datetime(df_chart['data_vencimento'])

    # Filtro de Mes/Ano
    ano_f = int(mes_sel.split('/')[1])
    mes_f = int(mes_sel.split('/')[0])

    df_filtrado = df_chart[
        (df_chart['data_vencimento'].dt.month == mes_f) &
        (df_chart['data_vencimento'].dt.year == ano_f) &
        (df_chart['natureza'].isin(natureza_sel)) &
        (df_chart['tipo'].isin(tipo_sel))
        ]

    if df_filtrado.empty:
        st.info("Não há dados para os filtros selecionados.")
        return

    # --- KPIS PRINCIPAIS ---
    receitas = df_filtrado[df_filtrado['tipo'] == 'Receita']['valor'].sum()
    despesas = df_filtrado[df_filtrado['tipo'] == 'Despesa']['valor'].sum()
    saldo = receitas - despesas

    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas no Período", f"R$ {receitas:,.2f}")
    c2.metric("Despesas no Período", f"R$ {despesas:,.2f}")
    c3.metric("Saldo do Filtro", f"R$ {saldo:,.2f}")

    st.divider()

    # --- GRÁFICOS ---
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.write("### Despesas por Categoria")
        df_cat = df_filtrado[df_filtrado['tipo'] == 'Despesa'].groupby('categoria')['valor'].sum().reset_index()
        fig_pizza = px.pie(df_cat, values='valor', names='categoria', hole=0.4,
                           color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pizza, use_container_width=True)

    with col_g2:
        st.write("### Natureza dos Lançamentos")
        fig_bar = px.bar(df_filtrado, x='natureza', y='valor', color='tipo',
                         barmode='group', labels={'valor': 'Total (R$)'},
                         color_discrete_map={'Receita': '#00CC96', 'Despesa': '#EF553B'})
        st.plotly_chart(fig_bar, use_container_width=True)

    st.write("### Evolução Diária (Vencimentos)")
    df_evol = df_filtrado.groupby(['data_vencimento', 'tipo'])['valor'].sum().reset_index()
    fig_evol = px.line(df_evol, x='data_vencimento', y='valor', color='tipo',
                       markers=True, line_shape='spline',
                       color_discrete_map={'Receita': '#00CC96', 'Despesa': '#EF553B'})
    st.plotly_chart(fig_evol, use_container_width=True)