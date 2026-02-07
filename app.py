import streamlit as st
import pandas as pd
from datetime import datetime
import os
import calendar

# --- [H10] IMPORTAÇÃO DO GERENCIADOR DE TEMAS E SERVIÇOS ---
from utils.theme_manager import ThemeManager
from services.database import Database
from ui.components import seletor_meses_inteligente
from ui.lancamentos_page import lancamentos_page
from ui.resumo_mensal_page import resumo_mensal_page

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

# =====================================================
# 2. CÁLCULOS GLOBAIS [H8.1 Saldo em Tempo Real]
# =====================================================
saldo_atual_contas = Database.obter_total_saldos_real()

if not st.session_state.df.empty:
    df_calc = st.session_state.df.copy()
    df_calc['valor'] = pd.to_numeric(df_calc['valor'], errors='coerce').fillna(0)
    pendente_pagar = df_calc[(df_calc['tipo'] == "Despesa") & (df_calc.get('status', '') != "🟢 Concluído")][
        'valor'].sum()
    pendente_receber = df_calc[(df_calc['tipo'] == "Receita") & (df_calc.get('status', '') != "🟢 Concluído")][
        'valor'].sum()
    saldo_disponivel = saldo_atual_contas
else:
    saldo_disponivel, pendente_pagar, pendente_receber = saldo_atual_contas, 0.0, 0.0

# =====================================================
# 3. SIDEBAR (MENU)
# =====================================================
with st.sidebar:
    tema_atual = st.session_state.get("tema", "padrão")
    logo_path = "assets/logo_light.png" if tema_atual == "padrão" else "assets/logo_dark.png"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.title("💎 PlanejAI")

    st.write("---")
    if st.button("📈 Resumo Mensal"): st.session_state.pagina = "Resumo"
    if st.button("➕ Gerenciar Lançamentos"): st.session_state.pagina = "Lançamento"
    if st.button("💰 Meus Saldos"): st.session_state.pagina = "Saldos"
    if st.button("🎯 Inteligência Financeira"): st.session_state.pagina = "Inteligencia_Financeira"
    if st.button("📄 Exportar Relatórios"): st.session_state.pagina = "Exportacao"
    if st.button("🤖 IA Consultora"): st.session_state.pagina = "IA"
    if st.button("⚙️ Configurações"): st.session_state.pagina = "Config"

    st.write("---")
    st.metric("Saldo em Contas", f"R$ {saldo_disponivel:,.2f}")
    if pendente_pagar > 0: st.caption(f"🔴 **A Pagar:** R$ {pendente_pagar:,.2f}")
    if pendente_receber > 0: st.caption(f"🟢 **A Receber:** R$ {pendente_receber:,.2f}")

# =====================================================
# 4. ROTEAMENTO
# =====================================================
df_display = st.session_state.df.copy()
if '_id' in df_display.columns:
    df_display = df_display.drop(columns=['_id'])

if st.session_state.pagina == "Resumo":
    resumo_mensal_page(df_display)

elif st.session_state.pagina == "Lançamento":
    lancamentos_page(st.session_state.df)

elif st.session_state.pagina == "Saldos":
    from ui.saldos_page import saldos_page

    saldos_page()

elif st.session_state.pagina == "Inteligencia_Financeira":
    analise_categorias_page(df_display)

elif st.session_state.pagina == "Exportacao":
    try:
        from ui.exportacao_page import exportacao_page
        exportacao_page(df_display)
    except Exception as e:
        st.error(f"Erro ao carregar a página de exportação: {e}")

elif st.session_state.pagina == "IA":
    from ui.ia_page import ia_page

    ia_page(df_display)

elif st.session_state.pagina == "Config":
    st.header("⚙️ Configurações")

    # --- BLOCO 1: TEMAS ---
    with st.container(border=True):
        novas_cores = st.session_state.theme_manager.sidebar_theme_selector()
        if novas_cores != st.session_state.theme_colors:
            st.session_state.theme_colors = novas_cores
            Database.salvar_preferencias(novas_cores)
            st.rerun()

    # --- BLOCO 2: CLONAGEM INTELIGENTE (RESTAURADO E SEGURO) ---
    with st.container(border=True):
        st.subheader("🔄 Clonagem Inteligente")
        st.info("Esta operação copia os lançamentos para o mês seguinte sem apagar os atuais.")

        col_sel, col_btn = st.columns([2, 1])

        with col_sel:
            # Seletor inteligente para escolher o mês de ORIGEM
            mes_origem_str = seletor_meses_inteligente(key_suffix="config_clonagem")

        with col_btn:
            st.write(" ")  # Espaçador para alinhar com o seletor
            if st.button("🚀 Executar Clonagem", type="primary", use_container_width=True):
                try:
                    # 1. Extrai Mês e Ano de Origem
                    m_o, a_o = map(int, mes_origem_str.split('/'))

                    # 2. Define Mês e Ano de Destino
                    m_d = m_o + 1 if m_o < 12 else 1
                    a_d = a_o if m_o < 12 else a_o + 1

                    # 3. Filtra os dados diretamente do cache atual
                    df_base = st.session_state.df.copy()
                    df_base['data_vencimento'] = pd.to_datetime(df_base['data_vencimento'])

                    mask = (df_base['data_vencimento'].dt.month == m_o) & (df_base['data_vencimento'].dt.year == a_o)
                    dados_origem = df_base[mask].copy()

                    if not dados_origem.empty:
                        # --- LIMPEZA DE SEGURANÇA ---
                        # Remove IDs do MongoDB para garantir que novos documentos sejam criados
                        if '_id' in dados_origem.columns:
                            dados_origem.drop(columns=['_id'], inplace=True)

                        # Reseta status para Pendente (novo mês, nova jornada)
                        dados_origem['status'] = "🟡 Pendente"


                        # --- ROTAÇÃO DE DATA SEGURA ---
                        def rotacionar_data(dt):
                            import calendar
                            # Tenta manter o mesmo dia, se o mês de destino não tiver esse dia, usa o último dia disponível
                            ultimo_dia_destino = calendar.monthrange(a_d, m_d)[1]
                            dia_seguro = min(dt.day, ultimo_dia_destino)
                            return dt.replace(year=a_d, month=m_d, day=dia_seguro)


                        dados_origem['data_vencimento'] = dados_origem['data_vencimento'].apply(rotacionar_data)

                        # 4. Gravação no MongoDB (Utilizando o novo método aditivo)
                        registros_clonados = dados_origem.to_dict('records')

                        if Database.inserir_muitos(registros_clonados):
                            st.success(
                                f"✅ Sucesso! {len(registros_clonados)} itens clonados de {mes_origem_str} para {m_d:02d}/{a_d}.")
                            # Atualiza o estado global para refletir os novos dados
                            st.session_state.df = Database.carregar_dados()
                            st.rerun()
                    else:
                        st.warning(f"Nenhum lançamento encontrado em {mes_origem_str} para clonar.")

                except Exception as e:
                    st.error(f"⚠️ Erro durante a clonagem: {e}")