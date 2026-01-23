import streamlit as st
from domain.resumo import resumo_mensal
from services.calendar_service import mes_ano


def resumo_page(df):
    st.header("📊 Resumo Financeiro")

    # Filtro de Meses
    opcoes = mes_ano()
    mes_selecionado = st.selectbox("Selecione o período:", opcoes)

    receitas, despesas, saldo = resumo_mensal(df, mes_selecionado)

    # Exibição em Cartões (Metrics)
    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", f"R$ {receitas:,.2f}")
    c2.metric("Despesas", f"R$ {despesas:,.2f}")
    c3.metric("Saldo Atual", f"R$ {saldo:,.2f}", delta=float(saldo))

    if not df.empty:
        st.subheader("Extrato Detalhado")
        st.dataframe(df, use_container_width=True)