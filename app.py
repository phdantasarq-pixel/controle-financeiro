import streamlit as st
import pandas as pd
from datetime import datetime
from ui.resumo_page import resumo_page
from services.database import Database
from utils.datas import formatar_data_br

# Configurações Iniciais
st.set_page_config(page_title="Meu Controle Financeiro", layout="wide")

# --- GERENCIAMENTO DE DADOS ---
if 'df' not in st.session_state:
    st.session_state.df = Database.carregar_dados()


def adicionar_lancamento(data_vencimento, tipo, natureza, valor, categoria, descricao):
    # 1. A data atual de salvamento é gerada automaticamente (sem input do usuário)
    data_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    novo_dado = pd.DataFrame([{
        'data_registro': data_registro,  # Campo oculto (data atual)
        'data_vencimento': pd.to_datetime(data_vencimento),  # Campo de vencimento
        'tipo': tipo,
        'natureza': natureza,  # Novo campo: Fixo/Variável
        'valor': float(valor),
        'categoria': categoria,
        'descricao': descricao
    }])

    st.session_state.df = pd.concat([st.session_state.df, novo_dado], ignore_index=True)
    Database.salvar_dados(st.session_state.df)


# --- BARRA LATERAL ---
st.sidebar.title("💰 Controle XP")
menu = st.sidebar.radio("Navegar para:", ["Resumo", "Novo Lançamento", "Configurações"])

if menu == "Resumo":
    resumo_page(st.session_state.df)

elif menu == "Novo Lançamento":
    st.header("📝 Novo Lançamento")

    with st.form("form_lancamento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            # 2. Campo Data de Vencimento (Padrão BR)
            vencimento = st.date_input("Data de Vencimento", value=datetime.now(), format="DD/MM/YYYY")
            tipo = st.selectbox("Tipo", ["Receita", "Despesa"])

        with col2:
            # 3. Campo Natureza (Fixo/Variável)
            natureza = st.selectbox("Natureza", ["Fixo", "Variável"])
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)

        categoria = st.text_input("Categoria (ex: Aluguel, Salário)")
        descricao = st.text_area("Descrição")
        submit = st.form_submit_button("Salvar Lançamento")

        if submit:
            if valor > 0:
                adicionar_lancamento(vencimento, tipo, natureza, valor, categoria, descricao)
                st.success(f"✅ Lançamento de {formatar_data_br(vencimento)} salvo com sucesso!")
            else:
                st.error("O valor deve ser maior que zero.")

elif menu == "Configurações":
    st.header("⚙️ Configurações")
    if st.button("Limpar Todos os Dados"):
        st.session_state.df = pd.DataFrame(
            columns=['data_registro', 'data_vencimento', 'tipo', 'natureza', 'valor', 'categoria', 'descricao'])
        Database.salvar_dados(st.session_state.df)
        st.rerun()