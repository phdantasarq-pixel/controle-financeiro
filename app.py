import streamlit as st

# =========================
# Services
# =========================
from services.storage import carregar_dados, salvar_dados

# =========================
# UI Pages
# =========================
from ui.despesas_page import despesas_page
from ui.receitas_page import receitas_page
from ui.resumo_page import resumo_page

# =========================
# Configuração da página
# =========================
st.set_page_config(
    page_title="Controle Financeiro 2026",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Estado Global (Session)
# =========================
if "dados" not in st.session_state:
    st.session_state.dados = carregar_dados()

dados = st.session_state.dados

# =========================
# Sidebar - Menu Principal
# =========================
st.sidebar.title("💰 Controle Financeiro")

menu = st.sidebar.radio(
    "Menu",
    [
        "📉 Despesas",
        "💵 A Receber",
        "📊 Resumo Mensal"
    ]
)

st.sidebar.divider()

st.sidebar.caption("Planejamento financeiro • MVP Streamlit")

# =========================
# Renderização das páginas
# =========================
if menu == "📉 Despesas":
    despesas_page(dados)

elif menu == "💵 A Receber":
    receitas_page(dados)

elif menu == "📊 Resumo Mensal":
    resumo_page(dados)

# =========================
# Persistência (manual)
# =========================
st.sidebar.divider()

if st.sidebar.button("💾 Salvar dados"):
    salvar_dados(st.session_state.dados)
    st.sidebar.success("Dados salvos com sucesso!")
