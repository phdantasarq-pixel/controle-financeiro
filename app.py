import streamlit as st
import pandas as pd
from ui.resumo_page import resumo_page
from ui.dashboard_page import dashboard_page
from services.database import Database
import os

# --- CONFIGURAÇÃO PlanejAI ---
st.set_page_config(page_title="PlanejAI", page_icon="💎", layout="wide")

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
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    st.title("PlanejAI")
    st.caption("Seu Consultor Financeiro Inteligente")
    st.write("---")

    if st.button("📊 Resumo Financeiro"): st.session_state.pagina = "Resumo"
    if st.button("➕ Novo Lançamento"): st.session_state.pagina = "Lançamento"
    if st.button("📈 Dashboard"): st.session_state.pagina = "Dashboard"
    if st.button("⚙️ Configurações"): st.session_state.pagina = "Config"

    st.write("---")
    total = st.session_state.df['valor'].sum() if not st.session_state.df.empty else 0
    st.metric("Patrimônio Geral", f"R$ {total:,.2f}")

# --- ROTEAMENTO ---
if st.session_state.pagina == "Resumo":
    resumo_page(st.session_state.df)

elif st.session_state.pagina == "Lançamento":
    st.header("📝 Novo Registro")
    categorias = ["Moradia", "Alimentação", "Transporte", "Lazer", "Saúde", "Educação", "Assinaturas", "Salário",
                  "Investimentos", "Outro"]

    # Criamos colunas para o formulário
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
        # O SEGREDO: O checkbox de parcelamento fora de um 'st.form' rígido
        # ou usando a re-execução do Streamlit
        is_parcelado = st.checkbox("Parcelar este lançamento?")

        num_parcelas = 1
        if is_parcelado:
            num_parcelas = st.number_input("Qtd de Parcelas", min_value=2, max_value=60, value=2)
            valor_individual = valor / num_parcelas
            st.info(f"O PlanejAI criará {num_parcelas} lançamentos de R$ {valor_individual:,.2f}")

        if st.button("🚀 Salvar no PlanejAI", use_container_width=True):
            if not descricao:
                st.error("Por favor, preencha a descrição.")
            else:
                final_cat = cat_outra if cat_sel == "Outro" else cat_sel
                novos_dados = []
                valor_parcela = valor / num_parcelas

                for i in range(num_parcelas):
                    # Calcula o mês subsequente
                    vencimento = pd.to_datetime(data_base) + pd.DateOffset(months=i)
                    desc_final = f"{descricao} ({i + 1}/{num_parcelas})" if num_parcelas > 1 else descricao

                    novos_dados.append({
                        "data_vencimento": vencimento,
                        "tipo": tipo,
                        "natureza": natureza,
                        "valor": valor_parcela,
                        "categoria": final_cat,
                        "descricao": desc_final
                    })

                # Concatena e salva
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(novos_dados)], ignore_index=True)
                Database.salvar_dados(st.session_state.df)
                st.success(f"Sucesso! {num_parcelas} lançamentos registrados.")
                st.rerun()

elif st.session_state.pagina == "Dashboard":
    dashboard_page(st.session_state.df)

elif st.session_state.pagina == "Config":
    st.header("⚙️ Configurações e Automação")
    st.subheader("🚀 Clonagem de Fixos")
    from services.calendar_service import mes_ano
    from datetime import datetime

    opcoes = mes_ano()
    mes_origem = st.selectbox("Clonar do mês:", opcoes, index=opcoes.index(datetime.now().strftime("%m/%Y")))

    if st.button("Executar Clonagem"):
        df = st.session_state.df.copy()
        df['data_vencimento'] = pd.to_datetime(df['data_vencimento'], format='mixed')
        m, a = map(int, mes_origem.split('/'))

        fixos = df[(df['data_vencimento'].dt.month == m) & (df['data_vencimento'].dt.year == a) & (
                    df['natureza'] == "Fixo")].copy()

        if not fixos.empty:
            fixos['data_vencimento'] = fixos['data_vencimento'] + pd.DateOffset(months=1)
            st.session_state.df = pd.concat([st.session_state.df, fixos], ignore_index=True)
            Database.salvar_dados(st.session_state.df)
            st.success(f"✅ {len(fixos)} itens clonados!")
            st.balloons()
        else:
            st.warning("Nenhum item fixo encontrado.")