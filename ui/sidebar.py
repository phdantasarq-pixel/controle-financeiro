import streamlit as st
from services.calendar_service import mes_ano

def render_sidebar():
    st.sidebar.title("📅 Navegação")

    menu = st.sidebar.radio(
        "Menu",
        ["Lançamentos", "Resumo Mensal", "Planejamento"]
    )

    meses = mes_ano()
    mes_atual = st.sidebar.selectbox("Mês", meses)

    return menu, mes_atual
