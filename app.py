import streamlit as st
import pandas as pd
from ui.resumo_page import resumo_page
from ui.dashboard_page import dashboard_page
from services.database import Database

# --- CONFIGURAÇÃO DA PÁGINA (PlanejAI) ---
st.set_page_config(page_title="PlanejAI", page_icon="💎", layout="wide")

# --- CSS PARA UX MODERNA (MENU LATERAL) ---
st.markdown("""
    <style>
        /* Remove o menu padrão do Streamlit para um visual mais limpo */
        [data-testid="stSidebarNav"] {display: none;}

        /* Estilização dos botões do menu lateral para parecerem blocos */
        .stButton button {
            width: 100%;
            border-radius: 8px;
            height: 3.5em;
            background-color: transparent;
            text-align: left;
            border: 1px solid rgba(151, 166, 195, 0.2);
            padding-left: 15px;
            margin-bottom: 10px;
            transition: 0.3s;
        }
        .stButton button:hover {
            border: 1px solid #28a745;
            background-color: rgba(40, 167, 69, 0.05);
        }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DO ESTADO ---
if 'df' not in st.session_state:
    st.session_state.df = Database.carregar_dados()
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Resumo"

# --- SIDEBAR (NOVA UX) ---
with st.sidebar:
    st.title("💎 PlanejAI")
    st.caption("Seu Consultor Financeiro Inteligente")
    st.write("---")

    # Navegação por botões (substituindo o Radio)
    if st.button("📊 Resumo Financeiro"): st.session_state.pagina = "Resumo"
    if st.button("➕ Novo Lançamento"): st.session_state.pagina = "Lançamento"
    if st.button("📈 Dashboard"): st.session_state.pagina = "Dashboard"
    if st.button("⚙️ Configurações"): st.session_state.pagina = "Config"

    st.write("---")
    # Widget de Saldo Rápido
    saldo_total = st.session_state.df['valor'].sum() if not st.session_state.df.empty else 0
    st.metric("Patrimônio Geral", f"R$ {saldo_total:,.2f}")

# --- ROTEAMENTO DE PÁGINAS ---
if st.session_state.pagina == "Resumo":
    resumo_page(st.session_state.df)

elif st.session_state.pagina == "Lançamento":
    st.header("📝 Novo Registro")

    # LISTA DE CATEGORIAS PADRONIZADAS (História de Usuário 1.1)
    cats_sugeridas = [
        "Moradia", "Alimentação", "Transporte", "Lazer",
        "Saúde", "Educação", "Assinaturas", "Salário",
        "Investimentos", "Freelance", "Outro"
    ]

    with st.form("form_lancamento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data = st.date_input("Vencimento", format="DD/MM/YYYY")
            tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
            valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01)

        with col2:
            natureza = st.selectbox("Natureza", ["Fixo", "Variável"])
            cat_selecionada = st.selectbox("Categoria", cats_sugeridas)
            cat_personalizada = st.text_input("Se 'Outro', especifique:")

        descricao = st.text_input("Descrição (Ex: Aluguel Janeiro)")

        # Logica de Parcelas (Placeholder para o próximo passo)
        parcelado = st.checkbox("Este lançamento é parcelado?")
        if parcelado:
            qtd_parcelas = st.number_input("Quantidade de Parcelas", min_value=2, max_value=48, value=2)

        if st.form_submit_button("Salvar Lançamento"):
            # Lógica para definir a categoria final
            categoria_final = cat_personalizada if cat_selecionada == "Outro" and cat_personalizada else cat_selecionada

            # Aqui você deve chamar a função de salvar no banco de dados
            st.success(f"Lançamento '{descricao}' em '{categoria_final}' salvo com sucesso!")

elif st.session_state.pagina == "Dashboard":
    dashboard_page(st.session_state.df)

elif st.session_state.pagina == "Config":
    st.header("⚙️ Configurações e Automações")
    st.write("Em breve: Clonagem de despesas fixas e integração com IA.")