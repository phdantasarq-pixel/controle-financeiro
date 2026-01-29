import streamlit as st
import pandas as pd
from datetime import datetime
from ui.resumo_page import resumo_page
from ui.dashboard_page import dashboard_page
from services.database import Database
import os

# --- CONFIGURAÇÃO PlanejAI ---
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

    if st.button("📊 Resumo Financeiro"): st.session_state.pagina = "Resumo"
    if st.button("➕ Novo Lançamento"): st.session_state.pagina = "Lançamento"
    if st.button("📈 Dashboard"): st.session_state.pagina = "Dashboard"
    if st.button("🤖 IA Consultora"): st.session_state.pagina = "IA"
    if st.button("⚙️ Configurações"): st.session_state.pagina = "Config"

    st.write("---")

    # Cálculo do Saldo Acumulado Real
    if not st.session_state.df.empty:
        df_calc = st.session_state.df.copy()
        receitas = df_calc[df_calc['tipo'] == "Receita"]['valor'].sum()
        despesas = df_calc[df_calc['tipo'] == "Despesa"]['valor'].sum()
        saldo_real = receitas - despesas
    else:
        saldo_real = 0.0

    st.metric("Saldo Acumulado", f"R$ {saldo_real:,.2f}", help="Total histórico: Receitas menos Despesas.")

def salvar_lancamento(valor, tipo, natureza, cat_sel, cat_outra, descricao, num_parcelas, data_base):
    with st.spinner("Sincronizando com MongoDB..."):
        final_cat = cat_outra if cat_sel == "Outro" else cat_sel
        valor_p = round(valor / num_parcelas, 2)
        data_hoje = datetime.now().strftime('%Y-%m-%d')

        novos = []
        for i in range(num_parcelas):
            venc = pd.to_datetime(data_base) + pd.DateOffset(months=i)
            desc_f = f"{descricao} ({i + 1}/{num_parcelas})" if num_parcelas > 1 else descricao
            novos.append({
                "data_vencimento": venc,
                "data_registro": data_hoje,
                "tipo": tipo,
                "natureza": natureza,
                "valor": valor_p,
                "categoria": final_cat,
                "descricao": desc_f
            })

        df_novos = pd.DataFrame(novos)
        # Sincronização e Blindagem
        colunas = ["data_vencimento", "data_registro", "tipo", "natureza", "valor", "categoria", "descricao"]
        for col in colunas:
            if col not in df_novos.columns: df_novos[col] = None

        df_novos["data_vencimento"] = pd.to_datetime(df_novos["data_vencimento"])
        df_novos["valor"] = df_novos["valor"].astype(float)

        st.session_state.df = pd.concat([st.session_state.df, df_novos], ignore_index=True)
        Database.salvar_dados(st.session_state.df)
    st.success("Lançamento concluído!")

# --- ROTEAMENTO ---
if st.session_state.pagina == "Resumo":
    resumo_page(st.session_state.df)

elif st.session_state.pagina == "Lançamento":
    st.header("📝 Novo Registro")
    categorias = ["Moradia", "Alimentação", "Transporte", "Lazer", "Saúde", "Educação", "Assinaturas", "Salário", "Investimentos", "Outro"]

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

        # --- DENTRO DO ROTEAMENTO: elif st.session_state.pagina == "Lançamento": ---

        # --- LOGICA DE SALVAMENTO COM TRAVA DE SEGURANÇA (H4.2) ---

        # 1. Botão Principal
        if st.button("🚀 Salvar no PlanejAI", use_container_width=True):
            if not descricao:
                st.error("Por favor, preencha a descrição.")
            else:
                df_atual = st.session_state.df
                receitas = df_atual[df_atual['tipo'] == "Receita"]['valor'].sum()
                despesas = df_atual[df_atual['tipo'] == "Despesa"]['valor'].sum()
                saldo_atual = receitas - despesas

                impacto = valor if tipo == "Despesa" else 0
                saldo_projetado = saldo_atual - impacto

                if tipo == "Despesa" and saldo_projetado < 0:
                    st.session_state.aguardando_confirmacao = True
                    st.session_state.dados_pendentes = {
                        "valor": valor, "tipo": tipo, "natureza": natureza,
                        "cat_sel": cat_sel, "cat_outra": cat_outra,
                        "descricao": descricao, "num_parcelas": num_parcelas,
                        "data_base": data_base, "saldo_atual": saldo_atual,
                        "saldo_projetado": saldo_projetado
                    }
                    st.rerun()  # Força a interface a mostrar o alerta
                else:
                    salvar_lancamento(valor, tipo, natureza, cat_sel, cat_outra, descricao, num_parcelas, data_base)
                    st.rerun()

        # 2. Área de Confirmação (Só aparece se houver pendência)
        if st.session_state.get("aguardando_confirmacao"):
            st.write("---")
            dados = st.session_state.dados_pendentes

            with st.container(border=True):
                st.warning(
                    f"⚠️ **Atenção:** Este gasto de **R$ {dados['valor']:,.2f}** deixará seu saldo real negativo (**R$ {dados['saldo_projetado']:,.2f}**).")

                confirmar_check = st.checkbox("Estou ciente do impacto financeiro.")

                col_conf, col_canc = st.columns(2)

                if col_conf.button("✅ Confirmar Lançamento", disabled=not confirmar_check, use_container_width=True):
                    salvar_lancamento(
                        dados['valor'], dados['tipo'], dados['natureza'],
                        dados['cat_sel'], dados['cat_outra'], dados['descricao'],
                        dados['num_parcelas'], dados['data_base']
                    )
                    # Limpa tudo
                    st.session_state.aguardando_confirmacao = False
                    st.session_state.dados_pendentes = {}
                    st.success("Lançamento confirmado!")
                    st.rerun()

                if col_canc.button("❌ Cancelar", use_container_width=True):
                    st.session_state.aguardando_confirmacao = False
                    st.session_state.dados_pendentes = {}
                    st.rerun()

elif st.session_state.pagina == "Dashboard":
    dashboard_page(st.session_state.df)

elif st.session_state.pagina == "IA":
    from ui.ia_page import ia_page
    ia_page(st.session_state.df)

elif st.session_state.pagina == "Config":
    st.header("⚙️ Configurações e Automação")

    with st.container(border=True):
        st.subheader("🚀 Clonagem de Gastos Fixos")
        st.write("Replica os lançamentos 'Fixo' para o mês seguinte.")

        from services.calendar_service import mes_ano
        opcoes_meses = mes_ano()
        mes_atual = datetime.now().strftime("%m/%Y")

        mes_origem = st.selectbox("Clonar a partir do mês:", opcoes_meses, index=opcoes_meses.index(mes_atual))

        if st.button("Executar Clonagem Inteligente", use_container_width=True):
            with st.spinner("Clonando registros fixos..."):
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
                    st.success(f"✅ Clonagem concluída!")
                    st.balloons()
            st.rerun()

    st.write("---")
    st.caption("PlanejAI v1.0")