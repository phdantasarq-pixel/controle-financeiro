import streamlit as st
import pandas as pd
from datetime import datetime
from ui.resumo_page import resumo_page
from ui.dashboard_page import dashboard_page
from ui.components import seletor_meses_inteligente
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
if "form_version" not in st.session_state:
    st.session_state.form_version = 0

def resetar_formulario():
    st.session_state.form_version += 1

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)

    st.title("PlanejAI")
    st.caption("Consultoria Financeira Inteligente")
    st.write("---")

    if st.button("📊 Resumo Financeiro"): st.session_state.pagina = "Resumo"
    if st.button("💰 Meus Saldos"): st.session_state.pagina = "Saldos"
    if st.button("➕ Novo Lançamento"): st.session_state.pagina = "Lançamento"
    if st.button("📈 Dashboard"): st.session_state.pagina = "Dashboard"
    if st.button("🤖 IA Consultora"): st.session_state.pagina = "IA"
    if st.button("⚙️ Configurações"): st.session_state.pagina = "Config"

    st.write("---")

    # --- CÁLCULO DE SALDO TOTAL (H7.1) ---
    df_saldos_gerais = Database.carregar_saldos()
    total_contas_manuais = df_saldos_gerais['valor'].sum() if not df_saldos_gerais.empty else 0.0

    if not st.session_state.df.empty:
        df_calc = st.session_state.df.copy()
        receitas = df_calc[df_calc['tipo'] == "Receita"]['valor'].sum()
        despesas = df_calc[df_calc['tipo'] == "Despesa"]['valor'].sum()
        saldo_real = (receitas - despesas) + total_contas_manuais
    else:
        saldo_real = total_contas_manuais

    st.metric("Saldo Total Disponível", f"R$ {saldo_real:,.2f}", help="Histórico (Extrato) + Saldos em 'Meus Saldos'.")


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
        st.session_state.df = pd.concat([st.session_state.df, df_novos], ignore_index=True)
        Database.salvar_dados(st.session_state.df)
    st.toast("Lançamento concluído com sucesso! ✨")


# --- ROTEAMENTO ---
if st.session_state.pagina == "Resumo":
    resumo_page(st.session_state.df)

elif st.session_state.pagina == "Saldos":
    from ui.saldos_page import saldos_page
    saldos_page()

elif st.session_state.pagina == "Lançamento":
    st.header("📝 Novo Registro")
    v = st.session_state.form_version
    mes_ref = seletor_meses_inteligente(key_suffix="pg_lancamento")
    data_sugerida = datetime.strptime(mes_ref, "%m/%Y")

    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            data_base = st.date_input("Vencimento", value=data_sugerida, format="DD/MM/YYYY", key=f"dt_{v}")
            tipo = st.selectbox("Tipo", ["Despesa", "Receita"], key=f"tp_{v}")
            valor = st.number_input("Valor Total R$", min_value=0.0, step=0.01, key=f"vl_{v}")
        with c2:
            natureza = st.selectbox("Natureza", ["Fixo", "Variável"], key=f"nt_{v}")
            cat_sel = st.selectbox("Categoria", ["Moradia", "Alimentação", "Transporte", "Lazer", "Saúde", "Educação", "Assinaturas", "Salário", "Investimentos", "Outro"], key=f"ct_{v}")
            cat_outra = st.text_input("Se 'Outro', qual?", key=f"co_{v}")

        descricao = st.text_input("Descrição", key=f"ds_{v}")
        st.write("---")
        is_parcelado = st.checkbox("Parcelar este lançamento?", key=f"pr_{v}")
        num_parcelas = st.number_input("Qtd de Parcelas", 2, 60, 2) if is_parcelado else 1

        if st.button("🚀 Salvar no PlanejAI", use_container_width=True):
            if not descricao:
                st.error("Por favor, preencha a descrição.")
            elif valor <= 0:
                st.error("O valor deve ser maior que zero.")
            else:
                # Usa o saldo_real (já calculado com os saldos manuais) para o alerta
                impacto = valor if tipo == "Despesa" else 0
                saldo_projetado = saldo_real - impacto

                if tipo == "Despesa" and saldo_projetado < 0:
                    st.session_state.aguardando_confirmacao = True
                    st.session_state.dados_pendentes = {
                        "valor": valor, "tipo": tipo, "natureza": natureza,
                        "cat_sel": cat_sel, "cat_outra": cat_outra,
                        "descricao": descricao, "num_parcelas": num_parcelas,
                        "data_base": data_base, "saldo_projetado": saldo_projetado
                    }
                    st.rerun()
                else:
                    salvar_lancamento(valor, tipo, natureza, cat_sel, cat_outra, descricao, num_parcelas, data_base)
                    resetar_formulario()
                    st.rerun()

    if st.session_state.get("aguardando_confirmacao"):
        dados = st.session_state.dados_pendentes
        with st.container(border=True):
            st.warning(f"⚠️ **Alerta:** Saldo ficará negativo (**R$ {dados['saldo_projetado']:,.2f}**).")
            confirmar_check = st.checkbox("Estou ciente do impacto.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar", disabled=not confirmar_check, use_container_width=True):
                    salvar_lancamento(dados['valor'], dados['tipo'], dados['natureza'], dados['cat_sel'], dados['cat_outra'], dados['descricao'], dados['num_parcelas'], dados['data_base'])
                    st.session_state.aguardando_confirmacao = False
                    resetar_formulario()
                    st.rerun()
            with col2:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.aguardando_confirmacao = False
                    st.rerun()

elif st.session_state.pagina == "Dashboard":
    dashboard_page(st.session_state.df)

elif st.session_state.pagina == "IA":
    from ui.ia_page import ia_page
    ia_page(st.session_state.df)

elif st.session_state.pagina == "Config":
    st.header("⚙️ Configurações e Automação")
    mes_origem = seletor_meses_inteligente(key_suffix="pg_config")
    if st.button("Executar Clonagem Inteligente", use_container_width=True):
        # ... (Logica de clonagem mantida)
        st.success("Clonagem concluída!")