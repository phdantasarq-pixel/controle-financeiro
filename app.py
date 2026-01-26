import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from ui.resumo_page import resumo_page
from ui.dashboard_page import dashboard_page
from services.database import Database
import os

# --- 1. CONFIGURAÇÃO E IDENTIDADE ---
st.set_page_config(page_title="PlanejAI", page_icon="💎", layout="wide")

# CSS para Menu Lateral Moderno
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        .stButton button {
            width: 100%;
            border-radius: 8px;
            height: 3.5em;
            background-color: transparent;
            text-align: left;
            border: 1px solid rgba(151, 166, 195, 0.2);
            padding-left: 15px;
            margin-bottom: 10px;
        }
        .stButton button:hover {
            border: 1px solid #28a745;
            background-color: rgba(40, 167, 69, 0.05);
        }
        [data-testid="stSidebar"] [data-testid="stImage"] {
            padding: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. INICIALIZAÇÃO DE DADOS ---
if 'df' not in st.session_state:
    st.session_state.df = Database.carregar_dados()
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Resumo"

# --- 3. SIDEBAR (MENU PlanejAI) ---
with st.sidebar:
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.title("💎 PlanejAI")

    st.caption("Seu Consultor Financeiro Inteligente")
    st.write("---")

    if st.button("📊 Resumo Financeiro"): st.session_state.pagina = "Resumo"
    if st.button("➕ Novo Lançamento"): st.session_state.pagina = "Lançamento"
    if st.button("📈 Dashboard"): st.session_state.pagina = "Dashboard"
    if st.button("⚙️ Configurações"): st.session_state.pagina = "Config"

    st.write("---")
    total = st.session_state.df['valor'].sum() if not st.session_state.df.empty else 0
    st.metric("Patrimônio Geral", f"R$ {total:,.2f}")

# --- 4. ROTEAMENTO DE PÁGINAS ---
if st.session_state.pagina == "Resumo":
    resumo_page(st.session_state.df)

elif st.session_state.pagina == "Lançamento":
    st.header("📝 Novo Registro")

    categorias = ["Moradia", "Alimentação", "Transporte", "Lazer", "Saúde", "Educação", "Assinaturas", "Salário",
                  "Investimentos", "Outro"]

    with st.form("form_planejai", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data_base = st.date_input("Vencimento", format="DD/MM/YYYY")
            tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
            valor = st.number_input("Valor R$", min_value=0.01, step=0.01)

        with col2:
            natureza = st.selectbox("Natureza", ["Fixo", "Variável"])
            cat_sel = st.selectbox("Categoria", categorias)
            cat_outra = st.text_input("Se 'Outro', qual?")

        descricao = st.text_input("Descrição")

        st.write("---")
        is_parcelado = st.checkbox("Parcelar este lançamento?")
        num_parcelas = st.number_input("Qtd de Parcelas", min_value=2, max_value=60, value=2) if is_parcelado else 1

        if st.form_submit_button("Salvar no PlanejAI"):
            final_cat = cat_outra if cat_sel == "Outro" else cat_sel
            novos_dados = []

            for i in range(num_parcelas):
                vencimento = data_base + pd.DateOffset(months=i)
                desc_final = f"{descricao} ({i + 1}/{num_parcelas})" if num_parcelas > 1 else descricao

                novo_item = {
                    "data_vencimento": vencimento.strftime("%Y-%m-%d"),
                    "tipo": tipo,
                    "natureza": natureza,
                    "valor": valor if not is_parcelado else valor / num_parcelas,  # Valor total dividido ou cheio
                    "categoria": final_cat,
                    "descricao": desc_final
                }
                novos_dados.append(novo_item)

            # Adicionar ao DataFrame e Salvar
            novo_df = pd.DataFrame(novos_dados)
            st.session_state.df = pd.concat([st.session_state.df, novo_df], ignore_index=True)
            Database.salvar_dados(st.session_state.df)
            st.success(f"Lançamento(s) salvo(s)! {num_parcelas} registro(s) criado(s).")

elif st.session_state.pagina == "Dashboard":
    dashboard_page(st.session_state.df)

elif st.session_state.pagina == "Config":
    st.header("⚙️ Configurações")
    st.info("Módulo de Clonagem e IA em desenvolvimento.")