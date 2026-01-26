import streamlit as st
import pandas as pd
from datetime import datetime
from ui.resumo_page import resumo_page
from ui.dashboard_page import dashboard_page
from services.database import Database
import os

st.set_page_config(page_title="PlanejAI", page_icon="💎", layout="wide")

# CSS Estilizado
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        .stButton button {
            width: 100%; border-radius: 8px; height: 3.5em;
            background-color: transparent; text-align: left;
            border: 1px solid rgba(151, 166, 195, 0.2);
            padding-left: 15px; margin-bottom: 10px;
        }
        .stButton button:hover { border: 1px solid #28a745; background-color: rgba(40, 167, 69, 0.05); }
        [data-testid="stSidebar"] [data-testid="stImage"] { padding: 20px; }
    </style>
""", unsafe_allow_html=True)

if 'df' not in st.session_state:
    st.session_state.df = Database.carregar_dados()
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Resumo"

with st.sidebar:
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path): st.image(logo_path, use_container_width=True)
    st.title("PlanejAI")
    st.write("---")
    if st.button("📊 Resumo Financeiro"): st.session_state.pagina = "Resumo"
    if st.button("➕ Novo Lançamento"): st.session_state.pagina = "Lançamento"
    if st.button("📈 Dashboard"): st.session_state.pagina = "Dashboard"
    if st.button("⚙️ Configurações"): st.session_state.pagina = "Config"

    st.write("---")
    total = st.session_state.df['valor'].sum() if not st.session_state.df.empty else 0
    st.metric("Patrimônio Geral", f"R$ {total:,.2f}")

# Roteamento
if st.session_state.pagina == "Resumo":
    resumo_page(st.session_state.df)

elif st.session_state.pagina == "Lançamento":
    st.header("📝 Novo Registro")
    categorias = ["Moradia", "Alimentação", "Transporte", "Lazer", "Saúde", "Educação", "Assinaturas", "Salário",
                  "Investimentos", "Outro"]

    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            data_base = st.date_input("Vencimento", format="DD/MM/YYYY")
            tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
            valor = st.number_input("Valor Total R$", min_value=0.01, step=0.01)
        with c2:
            natureza = st.selectbox("Natureza", ["Fixo", "Variável"])
            cat_sel = st.selectbox("Categoria", categorias)
            cat_outra = st.text_input("Se 'Outro', qual?")

        descricao = st.text_input("Descrição")
        st.write("---")
        is_parcelado = st.checkbox("Parcelar este lançamento?")
        num_parcelas = st.number_input("Qtd de Parcelas", 2, 60, 2) if is_parcelado else 1

        if st.button("🚀 Salvar no PlanejAI", use_container_width=True):
            if not descricao:
                st.error("Preencha a descrição!")
            else:
                final_cat = cat_outra if cat_sel == "Outro" else cat_sel
                valor_p = round(valor / num_parcelas, 2)
                data_hoje = datetime.now().strftime('%Y-%m-%d')

                novos = []
                for i in range(num_parcelas):
                    venc = pd.to_datetime(data_base) + pd.DateOffset(months=i)
                    novos.append({
                        "data_vencimento": venc,
                        "data_registro": data_hoje,
                        "tipo": tipo, "natureza": natureza, "valor": valor_p,
                        "categoria": final_cat,
                        "descricao": f"{descricao} ({i + 1}/{num_parcelas})" if num_parcelas > 1 else descricao
                    })

                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(novos)], ignore_index=True)
                Database.salvar_dados(st.session_state.df)
                st.success("Lançamento concluído!")
                st.rerun()

elif st.session_state.pagina == "Dashboard":
    dashboard_page(st.session_state.df)

elif st.session_state.pagina == "Config":
    st.header("⚙️ Configurações")
    # (Código de clonagem pode ser inserido aqui conforme sua feature branch)