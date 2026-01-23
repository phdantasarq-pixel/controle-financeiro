import streamlit as st
from ui.sidebar import sidebar
from services.storage import carregar_mes, salvar_mes
from ui.despesas_page import despesas_page
from ui.receitas_page import receitas_page
from ui.resumo_page import resumo_page

st.set_page_config("Controle Financeiro", layout="wide")

ano, mes, pagina = sidebar()

dados = carregar_mes(ano, mes)

if pagina == "📌 Despesas":
    despesas_page(dados)
elif pagina == "💰 A Receber":
    receitas_page(dados)
elif pagina == "📊 Resumo Mensal":
    resumo_page(dados)

if st.sidebar.button("💾 Salvar mês"):
    salvar_mes(ano, mes, dados)
    st.sidebar.success("Dados salvos!")
