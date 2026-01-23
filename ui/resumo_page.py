import streamlit as st
from domain.resumo import resumo_mensal
from services.calendar import gerar_meses


def resumo_page(lancamentos):
    st.title("📊 Resumo Mensal")

    mes = st.selectbox("Mês", gerar_meses())
    r, d, s = resumo_mensal(lancamentos, mes)

    st.metric("Receitas", f"R$ {r:.2f}")
    st.metric("Despesas", f"R$ {d:.2f}")
    st.metric("Saldo", f"R$ {s:.2f}")
