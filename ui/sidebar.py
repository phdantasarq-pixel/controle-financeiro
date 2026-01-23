import streamlit as st

def sidebar():
    st.sidebar.title("📂 Navegação")

    ano = st.sidebar.selectbox("Ano", [2026])
    mes = st.sidebar.selectbox("Mês", list(range(1, 13)))

    pagina = st.sidebar.radio(
        "Menu",
        ["📌 Despesas", "💰 A Receber", "📊 Resumo Mensal", "📈 Dashboard"]
    )

    return ano, mes, pagina
