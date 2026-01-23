import streamlit as st
import pandas as pd
from datetime import datetime
from ui.resumo_page import resumo_page
from ui.dashboard_page import dashboard_page
from services.database import Database
from utils.datas import formatar_data_br

# =========================================================
# ⚙️ CONFIGURAÇÕES INICIAIS
# =========================================================
st.set_page_config(
    page_title="Meu Controle Financeiro",
    page_icon="💰",
    layout="wide"
)

# --- GERENCIAMENTO DE ESTADO (Session State) ---
# Carrega os dados do JSON assim que o app inicia
if 'df' not in st.session_state:
    st.session_state.df = Database.carregar_dados()


# =========================================================
# 🛠️ FUNÇÕES DE APOIO
# =========================================================
def adicionar_lancamento(data_vencimento, tipo, natureza, valor, categoria, descricao):
    """
    Processa a lógica de novo lançamento:
    - Gera data_registro automaticamente
    - Concatena ao DataFrame global
    - Salva fisicamente no dados.json
    """
    # Captura exato momento do registro
    data_registro = datetime.now()

    novo_dado = pd.DataFrame([{
        'data_registro': data_registro,
        'data_vencimento': pd.to_datetime(data_vencimento),
        'tipo': tipo,
        'natureza': natureza,
        'valor': float(valor),
        'categoria': categoria,
        'descricao': descricao
    }])

    # Atualiza o estado da aplicação
    st.session_state.df = pd.concat([st.session_state.df, novo_dado], ignore_index=True)

    # Persistência no arquivo JSON através da Service
    if Database.salvar_dados(st.session_state.df):
        return True
    return False


# =========================================================
# 📂 BARRA LATERAL (MENU DE NAVEGAÇÃO)
# =========================================================
with st.sidebar:
    st.title("💰 Controle Financeiro")
    st.divider()
    menu = st.sidebar.radio(
        "Navegar para:",
        ["Resumo", "Novo Lançamento", "Dashboard", "Configurações"],
        index=0
    )
    st.divider()
    st.info(f"Total de registros: {len(st.session_state.df)}")

# =========================================================
# 🚀 LÓGICA DE NAVEGAÇÃO (ROTEAMENTO)
# =========================================================

# --- TELA 1: RESUMO (Extrato Detalhado com Edição) ---
if menu == "Resumo":
    resumo_page(st.session_state.df)

# --- TELA 2: NOVO LANÇAMENTO (Formulário) ---
elif menu == "Novo Lançamento":
    st.header("📝 Novo Lançamento")
    st.write("Preencha os dados abaixo para registrar uma nova movimentação.")

    with st.form("form_lancamento", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            # Data de vencimento no padrão brasileiro visual
            vencimento = st.date_input(
                "Data de Vencimento",
                value=datetime.now(),
                format="DD/MM/YYYY"
            )
            tipo = st.selectbox("Tipo de Lançamento", ["Receita", "Despesa"])

        with col2:
            natureza = st.selectbox("Natureza", ["Fixo", "Variável"])
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)

        col3, col4 = st.columns([1, 2])
        with col3:
            categoria = st.text_input("Categoria (Ex: Aluguel, Salário)")
        with col4:
            descricao = st.text_area("Descrição / Observação", height=68)

        submit = st.form_submit_button("🚀 Salvar Lançamento")

        if submit:
            if valor > 0:
                sucesso = adicionar_lancamento(vencimento, tipo, natureza, valor, categoria, descricao)
                if sucesso:
                    st.success(f"Lançamento de {formatar_data_br(vencimento)} registrado com sucesso!")
                else:
                    st.error("Erro ao tentar salvar no arquivo dados.json.")
            else:
                st.error("O valor deve ser maior que zero.")

# --- TELA 3: DASHBOARD (Gráficos e Análise) ---
elif menu == "Dashboard":
    dashboard_page(st.session_state.df)

# --- TELA 4: CONFIGURAÇÕES (Manutenção) ---
elif menu == "Configurações":
    st.header("⚙️ Configurações do Sistema")
    st.subheader("Manutenção de Dados")

    st.warning("Atenção: A ação de limpar dados é irreversível.")
    if st.button("🗑️ Limpar Todos os Dados"):
        # Reinicia o DataFrame com as colunas corretas
        colunas = ['data_registro', 'data_vencimento', 'tipo', 'natureza', 'valor', 'categoria', 'descricao']
        st.session_state.df = pd.DataFrame(columns=colunas)

        # Sobrescreve o arquivo físico
        Database.salvar_dados(st.session_state.df)
        st.success("Banco de dados reiniciado com sucesso!")
        st.rerun()