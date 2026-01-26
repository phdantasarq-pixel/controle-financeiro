import streamlit as st
import pandas as pd
from datetime import datetime
from ui.resumo_page import resumo_page
from ui.dashboard_page import dashboard_page
from services.database import Database
import os

# --- CONFIGURAÇÃO PlanejAI ---
st.set_page_config(page_title="PlanejAI", page_icon="💎", layout="wide")

# CSS Estilizado para manter a identidade visual do PlanejAI
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

# Inicialização do Estado Global
if 'df' not in st.session_state:
    st.session_state.df = Database.carregar_dados()
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Resumo"

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)

    st.title("PlanejAI")
    st.caption("Consultoria Financeira Inteligente")
    st.write("---")

    # Navegação
    if st.button("📊 Resumo Financeiro"): st.session_state.pagina = "Resumo"
    if st.button("➕ Novo Lançamento"): st.session_state.pagina = "Lançamento"
    if st.button("📈 Dashboard"): st.session_state.pagina = "Dashboard"
    if st.button("⚙️ Configurações"): st.session_state.pagina = "Config"

    st.write("---")

    # Cálculo do Saldo Acumulado Real (Receitas - Despesas)
    if not st.session_state.df.empty:
        df_calc = st.session_state.df.copy()
        receitas = df_calc[df_calc['tipo'] == "Receita"]['valor'].sum()
        despesas = df_calc[df_calc['tipo'] == "Despesa"]['valor'].sum()
        saldo_real = receitas - despesas
    else:
        saldo_real = 0.0

    st.metric("Saldo Acumulado", f"R$ {saldo_real:,.2f}", help="Total histórico: Receitas menos Despesas.")

# --- ROTEAMENTO DE PÁGINAS ---
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

        # Lógica Reativa de Parcelamento
        is_parcelado = st.checkbox("Parcelar este lançamento?")
        num_parcelas = st.number_input("Qtd de Parcelas", 2, 60, 2) if is_parcelado else 1

        if st.button("🚀 Salvar no PlanejAI", use_container_width=True):
            if not descricao:
                st.error("Por favor, preencha a descrição do lançamento.")
            else:
                final_cat = cat_outra if cat_sel == "Outro" else cat_sel
                valor_p = round(valor / num_parcelas, 2)
                data_hoje = datetime.now().strftime('%Y-%m-%d')

                novos = []
                for i in range(num_parcelas):
                    venc = pd.to_datetime(data_base) + pd.DateOffset(months=i)
                    desc_final = f"{descricao} ({i + 1}/{num_parcelas})" if num_parcelas > 1 else descricao
                    novos.append({
                        "data_vencimento": venc,
                        "data_registro": data_hoje,
                        "tipo": tipo,
                        "natureza": natureza,
                        "valor": valor_p,
                        "categoria": final_cat,
                        "descricao": desc_final
                    })

                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(novos)], ignore_index=True)
                Database.salvar_dados(st.session_state.df)
                st.success(f"Lançamento de {num_parcelas} parcela(s) concluído com sucesso!")
                st.rerun()

elif st.session_state.pagina == "Dashboard":
    dashboard_page(st.session_state.df)

elif st.session_state.pagina == "Config":
    st.header("⚙️ Configurações e Automação")

    with st.container(border=True):
        st.subheader("🚀 Clonagem de Gastos Fixos")
        st.write("""
            Replica todos os lançamentos marcados como **'Fixo'** para o mês seguinte.
        """)

        from services.calendar_service import mes_ano

        opcoes_meses = mes_ano()
        mes_atual = datetime.now().strftime("%m/%Y")

        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            mes_origem = st.selectbox("Clonar a partir do mês:", opcoes_meses, index=opcoes_meses.index(mes_atual))

        if st.button("Executar Clonagem Inteligente", use_container_width=True):
            df = st.session_state.df.copy()
            df['data_vencimento'] = pd.to_datetime(df['data_vencimento'], errors='coerce')

            m_origem, a_origem = map(int, mes_origem.split('/'))
            mask_fixos = (df['data_vencimento'].dt.month == m_origem) & \
                         (df['data_vencimento'].dt.year == a_origem) & \
                         (df['natureza'] == "Fixo")

            df_fixos = df[mask_fixos].copy()

            if df_fixos.empty:
                st.warning(f"Nenhum lançamento 'Fixo' encontrado em {mes_origem}.")
            else:
                df_fixos['data_registro'] = datetime.now().strftime('%Y-%m-%d')
                df_fixos['data_vencimento'] = df_fixos['data_vencimento'] + pd.DateOffset(months=1)

                st.session_state.df = pd.concat([st.session_state.df, df_fixos], ignore_index=True)
                Database.salvar_dados(st.session_state.df)
                st.success(f"✅ {len(df_fixos)} lançamentos clonados com sucesso!")
                st.balloons()
                st.rerun()

    st.write("---")
    st.caption("PlanejAI v1.0 - Inteligência em Gestão Financeira")