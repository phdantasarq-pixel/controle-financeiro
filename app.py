import streamlit as st
import pandas as pd
from datetime import datetime
from ui.resumo_page import resumo_page

# Configurações Iniciais
st.set_page_config(page_title="Meu Controle Financeiro", layout="wide")

# --- GERENCIAMENTO DE DADOS ---
if 'df' not in st.session_state:
    # Inicializa com colunas padrão
    st.session_state.df = pd.DataFrame(columns=['data', 'tipo', 'valor', 'categoria', 'descricao'])


def adicionar_lancamento(data, tipo, valor, categoria, descricao):
    novo_dado = pd.DataFrame([{
        'data': pd.to_datetime(data),
        'tipo': tipo,
        'valor': float(valor),
        'categoria': categoria,
        'descricao': descricao
    }])
    st.session_state.df = pd.concat([st.session_state.df, novo_dado], ignore_index=True)


# --- BARRA LATERAL (MENU) ---
st.sidebar.title("💰 Controle XP")
menu = st.sidebar.radio("Navegar para:", ["Resumo", "Novo Lançamento", "Configurações"])

# --- LÓGICA DE NAVEGAÇÃO ---
if menu == "Resumo":
    resumo_page(st.session_state.df)

elif menu == "Novo Lançamento":
    st.header("📝 Novo Lançamento")

    with st.form("form_lancamento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data = st.date_input("Data", datetime.now())
            tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
        with col2:
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            categoria = st.text_input("Categoria (ex: Aluguel, Salário)")

        descricao = st.text_area("Descrição")
        submit = st.form_submit_button("Salvar Lançamento")

        if submit:
            if valor > 0:
                adicionar_lancamento(data, tipo, valor, categoria, descricao)
                st.success("Lançamento adicionado com sucesso!")
            else:
                st.error("O valor deve ser maior que zero.")

elif menu == "Configurações":
    st.header("⚙️ Configurações")
    if st.button("Limpar Todos os Dados"):
        st.session_state.df = pd.DataFrame(columns=['data', 'tipo', 'valor', 'categoria', 'descricao'])
        st.rerun()