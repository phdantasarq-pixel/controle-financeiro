import streamlit as st
from services.storage import carregar_dados
from ui.lancamentos_page import lancamentos_page
from ui.resumo_page import resumo_page
from ui.planejamento_page import planejamento_page

st.set_page_config(page_title="Controle Financeiro", layout="wide")

if "dados" not in st.session_state:
    st.session_state.dados = carregar_dados()

menu = st.sidebar.radio(
    "Menu",
    ["Lançamentos", "Resumo Mensal", "Planejamento"]
)

if menu == "Lançamentos":
    lancamentos_page(st.session_state.dados)
elif menu == "Resumo Mensal":
    resumo_page(st.session_state.dados)
else:
    planejamento_page(st.session_state.dados)
