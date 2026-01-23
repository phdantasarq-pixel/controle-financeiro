import streamlit as st
from domain.resumo import resumo_mensal

def resumo_page(dados):
    st.header("📊 Resumo Mensal")

    resumo = resumo_mensal(
        dados["despesas"],
        dados["receitas"]
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Fixos", f"R$ {resumo['fixos']:,.2f}")
    col2.metric("Variáveis", f"R$ {resumo['variaveis']:,.2f}")
    col3.metric("Total Despesas", f"R$ {resumo['total_despesas']:,.2f}")
    col4.metric("Total Receitas", f"R$ {resumo['total_receitas']:,.2f}")

    st.divider()
    st.metric("Resultado do mês", f"R$ {resumo['resultado']:,.2f}")
