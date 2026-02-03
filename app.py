import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- [H10] IMPORTAÇÃO DO GERENCIADOR DE TEMAS E SERVIÇOS ---
from utils.theme_manager import ThemeManager
from services.database import Database
from ui.resumo_page import resumo_page
from ui.dashboard_page import dashboard_page
from ui.components import seletor_meses_inteligente

# --- IMPORTAÇÃO DE PÁGINAS COM FALLBACK ---
try:
    from ui.exportacao_page import exportacao_page
except ImportError:
    def exportacao_page(df):
        st.warning("Página de Exportação não encontrada.")

try:
    from ui.analise_page import analise_categorias_page
except ImportError:
    def analise_categorias_page(df):
        st.warning("Página de Inteligência não encontrada.")

# =====================================================
# CONFIGURAÇÃO PlanejAI
# =====================================================
st.set_page_config(page_title="PlanejAI", page_icon="💎", layout="wide")

# --- [H10] INICIALIZAÇÃO DO TEMA VIA MONGODB ---
if 'theme_manager' not in st.session_state:
    st.session_state.theme_manager = ThemeManager()

if 'theme_colors' not in st.session_state:
    cores_salvas = Database.carregar_preferencias()
    # Padrão caso não exista no banco
    st.session_state.theme_colors = cores_salvas if cores_salvas else ("#4CAF50", "#FFFFFF", "#31333F", "#F0F2F6")

# APLICAÇÃO DO CSS DINÂMICO (Substitui todo o CSS removido)
st.markdown(
    st.session_state.theme_manager.get_theme_css(st.session_state.theme_colors),
    unsafe_allow_html=True
)

# Ajustes estruturais mínimos de layout (sem cores fixas)
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none;}
    #MainMenu, footer, [data-testid="stHeader"] { visibility: hidden; }
    .block-container { padding-top: 2rem; }
    [data-testid="stSidebar"] .stButton button {
        width: 100%; border-radius: 10px; height: 3.2em; text-align: left;
        padding-left: 15px; margin-bottom: 8px; display: flex; align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# 1. ESTADO GLOBAL E DADOS
# =====================================================
if 'df' not in st.session_state:
    st.session_state.df = Database.carregar_dados()

if 'pagina' not in st.session_state:
    st.session_state.pagina = "Resumo"

if "form_version" not in st.session_state:
    st.session_state.form_version = 0

if "aguardando_confirmacao" not in st.session_state:
    st.session_state.aguardando_confirmacao = False

# =====================================================
# 2. CÁLCULOS GLOBAIS [H8.1 Saldo em Tempo Real]
# =====================================================
df_saldos_manuais = Database.carregar_saldos()
total_contas_manuais = pd.to_numeric(df_saldos_manuais['valor'],
                                     errors='coerce').sum() if not df_saldos_manuais.empty else 0.0

if not st.session_state.df.empty:
    df_calc = st.session_state.df.copy()
    df_calc['valor'] = pd.to_numeric(df_calc['valor'], errors='coerce').fillna(0)
    if 'status' not in df_calc.columns: df_calc['status'] = 'Pendente'

    receitas_efetivadas = df_calc[(df_calc['tipo'] == "Receita") & (df_calc['status'] == "Concluído")]['valor'].sum()
    despesas_efetivadas = df_calc[(df_calc['tipo'] == "Despesa") & (df_calc['status'] == "Concluído")]['valor'].sum()

    saldo_real = (receitas_efetivadas - despesas_efetivadas) + total_contas_manuais
    pendente_pagar = df_calc[(df_calc['tipo'] == "Despesa") & (df_calc['status'] != "Concluído")]['valor'].sum()
    pendente_receber = df_calc[(df_calc['tipo'] == "Receita") & (df_calc['status'] != "Concluído")]['valor'].sum()
else:
    saldo_real, pendente_pagar, pendente_receber = total_contas_manuais, 0.0, 0.0


# =====================================================
# 3. FUNÇÕES DE LÓGICA (VALIDADAS)
# =====================================================
def resetar_formulario():
    st.session_state.form_version += 1
    if "dados_pendentes" in st.session_state: del st.session_state.dados_pendentes
    st.session_state.aguardando_confirmacao = False


def salvar_lancamento(valor, tipo, natureza, cat_sel, cat_outra, descricao, num_parcelas, data_base):
    with st.spinner("Sincronizando..."):
        final_cat = cat_outra if cat_sel == "Outro" else cat_sel
        valor_p = round(valor / num_parcelas, 2)
        novos = []
        for i in range(num_parcelas):
            venc = pd.to_datetime(data_base) + pd.DateOffset(months=i)
            novos.append({
                "data_vencimento": venc,
                "data_registro": datetime.now().strftime('%Y-%m-%d'),
                "tipo": tipo, "natureza": natureza, "valor": valor_p,
                "categoria": final_cat,
                "descricao": f"{descricao} ({i + 1}/{num_parcelas})" if num_parcelas > 1 else descricao,
                "status": "Pendente"
            })
        df_novos = pd.DataFrame(novos)
        df_novos["data_vencimento"] = pd.to_datetime(df_novos["data_vencimento"]).dt.tz_localize(None)
        st.session_state.df = pd.concat([st.session_state.df, df_novos], ignore_index=True)
        Database.salvar_dados(st.session_state.df)
    st.toast("Sucesso! ✨")


def executar_clonagem(mes_referencia):
    try:
        mes_f, ano_f = map(int, mes_referencia.split('/'))
        df = st.session_state.df.copy()
        df['data_vencimento'] = pd.to_datetime(df['data_vencimento'])
        fixos = df[(df['data_vencimento'].dt.month == mes_f) & (df['data_vencimento'].dt.year == ano_f) & (
                    df['natureza'] == "Fixo")].copy()
        if not fixos.empty:
            fixos['data_vencimento'] = fixos['data_vencimento'] + pd.DateOffset(months=1)
            fixos['status'] = "Pendente"
            if '_id' in fixos.columns: fixos.drop(columns=['_id'], inplace=True)
            st.session_state.df = pd.concat([st.session_state.df, fixos], ignore_index=True)
            Database.salvar_dados(st.session_state.df)
            st.success(f"✅ {len(fixos)} itens clonados!")
    except Exception as e:
        st.error(f"Erro: {e}")


# =====================================================
# 4. SIDEBAR
# =====================================================
with st.sidebar:
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path): st.image(logo_path, use_container_width=True)
    st.title("PlanejAI")
    st.write("---")

    if st.button("📊 Resumo Financeiro"): st.session_state.pagina = "Resumo"
    if st.button("💰 Meus Saldos"): st.session_state.pagina = "Saldos"
    if st.button("➕ Novo Lançamento"): st.session_state.pagina = "Lançamento"
    if st.button("📈 Dashboard"): st.session_state.pagina = "Dashboard"
    if st.button("🎯 Inteligência Financeira"): st.session_state.pagina = "Inteligencia_Financeira"
    if st.button("📄 Exportar Relatórios"): st.session_state.pagina = "Exportacao"
    if st.button("🤖 IA Consultora"): st.session_state.pagina = "IA"
    if st.button("⚙️ Configurações"): st.session_state.pagina = "Config"

    st.write("---")
    st.metric("Saldo Real Disponível", f"R$ {saldo_real:,.2f}")
    if pendente_pagar > 0: st.caption(f"🔴 **A Pagar:** R$ {pendente_pagar:,.2f}")
    if pendente_receber > 0: st.caption(f"🟢 **A Receber:** R$ {pendente_receber:,.2f}")

# =====================================================
# 5. ROTEAMENTO
# =====================================================
df_display = st.session_state.df.copy()
if '_id' in df_display.columns: df_display = df_display.drop(columns=['_id'])

if st.session_state.pagina == "Resumo":
    resumo_page(df_display)

elif st.session_state.pagina == "Saldos":
    from ui.saldos_page import saldos_page

    saldos_page()

elif st.session_state.pagina == "Lançamento":
    st.header("📝 Novo Registro")
    v = st.session_state.form_version
    mes_ref = seletor_meses_inteligente(key_suffix="pg_lanc")
    data_sugerida = datetime.strptime(mes_ref, "%m/%Y")

    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            data_base = st.date_input("Vencimento", value=data_sugerida, format="DD/MM/YYYY", key=f"dt_{v}")
            tipo = st.selectbox("Tipo", ["Despesa", "Receita"], key=f"tp_{v}")
            valor = st.number_input("Valor R$", min_value=0.0, step=0.01, key=f"vl_{v}")
        with c2:
            natureza = st.selectbox("Natureza", ["Fixo", "Variável"], key=f"nt_{v}")
            cat_sel = st.selectbox("Categoria",
                                   ["Moradia", "Alimentação", "Transporte", "Lazer", "Saúde", "Educação", "Assinaturas",
                                    "Salário", "Investimentos", "Cartão de Crédito", "Empréstimo", "Outro"],
                                   key=f"ct_{v}")
            cat_outra = st.text_input("Se 'Outro', qual?", key=f"co_{v}")

        descricao = st.text_input("Descrição", key=f"ds_{v}")
        is_parcelado = st.checkbox("Parcelar?", key=f"pr_{v}")
        num_parcelas = st.number_input("Qtd", 2, 60, 2) if is_parcelado else 1

        if st.button("🚀 Salvar", use_container_width=True):
            if not descricao or valor <= 0:
                st.error("Campos obrigatórios ausentes.")
            else:
                saldo_p = saldo_real - (valor if tipo == "Despesa" else 0)
                if tipo == "Despesa" and saldo_p < 0:
                    st.session_state.aguardando_confirmacao = True
                    st.session_state.dados_pendentes = {
                        "valor": valor, "tipo": tipo, "natureza": natureza, "cat_sel": cat_sel,
                        "cat_outra": cat_outra, "descricao": descricao, "num_parcelas": num_parcelas,
                        "data_base": data_base, "saldo_projetado": saldo_p
                    }
                    st.rerun()
                else:
                    salvar_lancamento(valor, tipo, natureza, cat_sel, cat_outra, descricao, num_parcelas, data_base)
                    resetar_formulario()
                    st.rerun()

    if st.session_state.get("aguardando_confirmacao"):
        dados = st.session_state.dados_pendentes
        with st.container(border=True):
            st.warning(f"⚠️ Saldo ficará negativo (R$ {dados['saldo_projetado']:,.2f}).")
            if st.button("✅ Confirmar"):
                salvar_lancamento(dados['valor'], dados['tipo'], dados['natureza'], dados['cat_sel'],
                                  dados['cat_outra'], dados['descricao'], dados['num_parcelas'], dados['data_base'])
                resetar_formulario()
                st.rerun()
            if st.button("❌ Cancelar"):
                resetar_formulario()
                st.rerun()

elif st.session_state.pagina == "Dashboard":
    dashboard_page(df_display)

elif st.session_state.pagina == "Inteligencia_Financeira":
    analise_categorias_page(df_display)

elif st.session_state.pagina == "Exportacao":
    exportacao_page(df_display)

elif st.session_state.pagina == "IA":
    from ui.ia_page import ia_page

    ia_page(df_display)

elif st.session_state.pagina == "Config":
    st.header("⚙️ Configurações")
    with st.container(border=True):
        novas_cores = st.session_state.theme_manager.sidebar_theme_selector()
        if novas_cores != st.session_state.theme_colors:
            st.session_state.theme_colors = novas_cores
            Database.salvar_preferencias(novas_cores)
            st.rerun()
    with st.container(border=True):
        st.subheader("🔄 Clonagem")
        mes_origem = seletor_meses_inteligente(key_suffix="cfg")
        if st.button("🚀 Executar Clonagem"):
            executar_clonagem(mes_origem)
            st.rerun()