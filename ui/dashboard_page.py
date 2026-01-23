import streamlit as st
import pandas as pd
import plotly.express as px
from services.calendar_service import mes_ano
from datetime import datetime


def dashboard_page(df):
    # --- ESTILIZAÇÃO CSS (Igual ao Resumo para consistência) ---
    st.markdown("""
        <style>
            div[data-testid="stSegmentedControl"] button {
                min-height: 55px;
                min-width: 80px;
                font-weight: bold;
                font-size: 16px;
            }
        </style>
    """, unsafe_allow_html=True)

    st.header("📈 Dashboard Analítico")

    if df.empty:
        st.warning("Nenhum dado disponível para análise.")
        return

    # --- NAVEGAÇÃO: MÊS DE REFERÊNCIA ---
    opcoes = mes_ano()
    mes_atual_str = datetime.now().strftime("%m/%Y")

    try:
        indice_padrao = opcoes.index(mes_atual_str)
    except ValueError:
        indice_padrao = 0

    st.write("### 📅 Mês de Referência")

    mes_selecionado = st.segmented_control(
        label="Meses Disponíveis",
        options=opcoes,
        default=opcoes[indice_padrao],
        selection_mode="single",
        label_visibility="collapsed"
    )

    if not mes_selecionado:
        mes_selecionado = mes_atual_str

    # --- FILTROS ADICIONAIS (Natureza e Tipo) ---
    st.write("---")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        natureza_sel = st.multiselect("Filtrar por Natureza:", options=["Fixo", "Variável"],
                                      default=["Fixo", "Variável"])
    with col_f2:
        tipo_sel = st.multiselect("Filtrar por Tipo:", options=["Receita", "Despesa"], default=["Receita", "Despesa"])

    # --- PROCESSAMENTO E FILTRAGEM ---
    df_chart = df.copy()
    df_chart['data_vencimento'] = pd.to_datetime(df_chart['data_vencimento'])

    # Extrair mês e ano do botão selecionado
    mes_f = int(mes_selecionado.split('/')[0])
    ano_f = int(mes_selecionado.split('/')[1])

    # Aplicar filtros: Mês de Referência + Natureza + Tipo
    mask = (
            (df_chart['data_vencimento'].dt.month == mes_f) &
            (df_chart['data_vencimento'].dt.year == ano_f) &
            (df_chart['natureza'].isin(natureza_sel)) &
            (df_chart['tipo'].isin(tipo_sel))
    )
    df_filtrado = df_chart[mask]

    if df_filtrado.empty:
        st.info(f"Não existem dados para os filtros selecionados em {mes_selecionado}.")
        return

    # --- KPIS PRINCIPAIS DO MÊS ---
    receitas = df_filtrado[df_filtrado['tipo'] == 'Receita']['valor'].sum()
    despesas = df_filtrado[df_filtrado['tipo'] == 'Despesa']['valor'].sum()
    saldo = receitas - despesas

    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas no Período", f"R$ {receitas:,.2f}")
    c2.metric("Despesas no Período", f"R$ {despesas:,.2f}")
    c3.metric("Saldo do Filtro", f"R$ {saldo:,.2f}", delta=f"R$ {saldo:,.2f}")

    st.divider()

    # --- GRÁFICOS ---
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.write("### 🍰 Despesas por Categoria")
        df_cat = df_filtrado[df_filtrado['tipo'] == 'Despesa'].groupby('categoria')['valor'].sum().reset_index()
        if not df_cat.empty:
            fig_pizza = px.pie(df_cat, values='valor', names='categoria', hole=0.4,
                               color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_pizza, use_container_width=True)
        else:
            st.write("Sem despesas para exibir.")

    with col_g2:
        st.write("### 📊 Natureza vs Tipo")
        fig_bar = px.bar(df_filtrado, x='natureza', y='valor', color='tipo',
                         barmode='group',
                         color_discrete_map={'Receita': '#00CC96', 'Despesa': '#EF553B'})
        st.plotly_chart(fig_bar, use_container_width=True)

    st.write("### 📅 Fluxo de Caixa Diário (Vencimentos)")
    df_evol = df_filtrado.groupby(['data_vencimento', 'tipo'])['valor'].sum().reset_index()
    fig_evol = px.line(df_evol, x='data_vencimento', y='valor', color='tipo',
                       markers=True,
                       color_discrete_map={'Receita': '#00CC96', 'Despesa': '#EF553B'})
    st.plotly_chart(fig_evol, use_container_width=True)