import streamlit as st
from services.calendar_service import meses_disponiveis

def render_sidebar():
    st.sidebar.title("📅 Navegação")

    menu = st.sidebar.radio(
        "Menu",
        ["Lançamentos", "Resumo Mensal", "Planejamento"]
    )

    meses = meses_disponiveis()
    mes_atual = st.sidebar.selectbox("Mês", meses)

    return menu, mes_atual
