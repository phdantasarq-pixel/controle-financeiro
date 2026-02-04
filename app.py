import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- [H10] IMPORTAÇÃO DO GERENCIADOR DE TEMAS E SERVIÇOS ---
from utils.theme_manager import ThemeManager
from services.database import Database
from ui.resumo_page import resumo_page
# AJUSTE: Importando o novo nome da função
from ui.resumo_mensal_page import resumo_mensal_page
from ui.components import seletor_meses_inteligente
from ui.lancamentos_page import lancamentos_page

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
    st.session_state.theme_colors = cores_salvas if cores_salvas else ("#4CAF50", "#FFFFFF", "#31333F", "#F0F2F6")

st.markdown(
    st.session_state.theme_manager.get_theme_css(st.session_state.theme_colors),
    unsafe_allow_html=True
)

st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none;}
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0) !important; color: inherit !important; }
    .block-container { padding-top: 2rem; }
    [data-testid="stSidebarContent"] .stButton button {
        width: 100%; border-radius: 10px; height: 3.2em; text-align: left;
        padding-left: 15px; margin-bottom: 8px; display: flex; align-items: center; opacity: 1 !important;
    }
    [data-testid="stSidebarContent"] .stButton p { font-weight: 500 !important; }
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
saldo_atual_contas = Database.obter_total_saldos_real()

if not st.session_state.df.empty:
    df_calc = st.session_state.df.copy()
    df_calc['valor'] = pd.to_numeric(df_calc['valor'], errors='coerce').fillna(0)
    if 'status' not in df_calc.columns:
        df_calc['status'] = '🟡 Pendente'

    pendente_pagar = df_calc[(df_calc['tipo'] == "Despesa") & (df_calc['status'] != "🟢 Concluído")]['valor'].sum()
    pendente_receber = df_calc[(df_calc['tipo'] == "Receita") & (df_calc['status'] != "🟢 Concluído")]['valor'].sum()
    saldo_disponivel = saldo_atual_contas
else:
    saldo_disponivel, pendente_pagar, pendente_receber = saldo_atual_contas, 0.0, 0.0

# =====================================================
# 3. SIDEBAR (MENU ATUALIZADO)
# =====================================================
with st.sidebar:
    # Lógica de Logo conforme tema homologado
    tema_atual = st.session_state.get("tema", "padrão")
    logo_path = "assets/logo_light.png" if tema_atual == "padrão" else "assets/logo_dark.png"
    st.sidebar.image(logo_path, use_container_width=True)

    st.write("---")

    # Atualização dos nomes nos botões do Menu
    if st.button("📊 Resumo de Lançamentos"): st.session_state.pagina = "Resumo"
    if st.button("💰 Meus Saldos"): st.session_state.pagina = "Saldos"
    if st.button("➕ Novo Lançamento"): st.session_state.pagina = "Lançamento"

    # AJUSTE: Nome do menu alterado para "Resumo Mensal"
    if st.button("📈 Resumo Mensal"): st.session_state.pagina = "ResumoMensal"

    if st.button("🎯 Inteligência Financeira"): st.session_state.pagina = "Inteligencia_Financeira"
    if st.button("📄 Exportar Relatórios"): st.session_state.pagina = "Exportacao"
    if st.button("🤖 IA Consultora"): st.session_state.pagina = "IA"
    if st.button("⚙️ Configurações"): st.session_state.pagina = "Config"

    st.write("---")
    st.metric("Saldo em Contas", f"R$ {saldo_disponivel:,.2f}")
    if pendente_pagar > 0: st.caption(f"🔴 **A Pagar:** R$ {pendente_pagar:,.2f}")
    if pendente_receber > 0: st.caption(f"🟢 **A Receber:** R$ {pendente_receber:,.2f}")

# =====================================================
# 4. ROTEAMENTO (ATUALIZADO)
# =====================================================
df_display = st.session_state.df.copy()
if '_id' in df_display.columns: df_display = df_display.drop(columns=['_id'])

if st.session_state.pagina == "Resumo":
    resumo_page(st.session_state.df)

elif st.session_state.pagina == "Saldos":
    from ui.saldos_page import saldos_page

    saldos_page()

elif st.session_state.pagina == "Lançamento":
    lancamentos_page(st.session_state.df)

# AJUSTE: Roteamento para a nova página e função
elif st.session_state.pagina == "ResumoMensal":
    resumo_mensal_page(df_display)

elif st.session_state.pagina == "Inteligencia_Financeira":
    analise_categorias_page(df_display)

elif st.session_state.pagina == "Exportacao":
    exportacao_page(df_display)

elif st.session_state.pagina == "IA":
    from ui.ia_page import ia_page

    ia_page(df_display)

elif st.session_state.pagina == "Config":
    # ... (restante do código de configuração mantido igual)
    st.header("⚙️ Configurações")
    with st.container(border=True):
        novas_cores = st.session_state.theme_manager.sidebar_theme_selector()
        if novas_cores != st.session_state.theme_colors:
            st.session_state.theme_colors = novas_cores
            Database.salvar_preferencias(novas_cores)
            st.rerun()