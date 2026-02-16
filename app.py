import streamlit as st
import pandas as pd
from datetime import datetime
import os
import calendar

# --- NOVO: IMPORTAÇÃO DO MÓDULO DE AUTENTICAÇÃO ---
from auth import login_page

# --- [H10] IMPORTAÇÃO DO GERENCIADOR DE TEMAS E SERVIÇOS ---
from utils.theme_manager import ThemeManager
from services.database import Database
from ui.components import seletor_meses_inteligente
from ui.lancamentos_page import lancamentos_page
from ui.resumo_mensal_page import resumo_mensal_page

from streamlit_cookies_manager import CookieManager

# --- IMPORTAÇÃO DE PÁGINAS COM FALLBACK ---
try:
    from ui.exportacao_page import exportacao_page
except ImportError:
    def exportacao_page(df):
        st.warning("Página de Exportação não encontrada.")

try:
    from ui.analise_page import analise_categorias_page
except ImportError:
    def analise_categorias_page(df, df_saldos=None):
        st.warning("Página de Inteligência não encontrada.")

# =====================================================
# CONFIGURAÇÃO PlanejAI (GLOBAL)
# =====================================================
st.set_page_config(page_title="PlanejAI", page_icon="💎", layout="wide")

# Inicializa o gerenciador de cookies
cookies = CookieManager()
if not cookies.ready():
    st.stop()

# Inicializa o estado de autenticação se não existir
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# --- LÓGICA DE PERSISTÊNCIA (F5) CORRIGIDA ---
token = cookies.get("auth_token")
# O token deve ser o próprio e-mail ou um ID único, não uma string fixa
if token and not st.session_state.authenticated:
    # Aqui o ideal é que o token contenha a informação de QUEM é o usuário
    user_data = Database.buscar_usuario(token) # Assumindo que o token é o e-mail
    if user_data:
        st.session_state.authenticated = True
        st.session_state.user_id = str(user_data.get("_id"))
        st.session_state.user_name = user_data.get("nome")
        # Força recarga dos dados para garantir isolamento
        st.session_state.df = Database.carregar_dados()
        st.rerun()

# =====================================================
# ROTEAMENTO: LOGIN OU SISTEMA
# =====================================================
if not st.session_state.authenticated:
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = "login"

    if st.session_state.auth_mode == "login":
        login_page(cookies) # Passando o objeto cookies para o auth.py
    else:
        from ui.signup_page import signup_page
        signup_page()
    st.stop()
else:
    # Verificação de segurança: Se autenticado, PRECISA ter user_id
    if 'user_id' not in st.session_state:
        # Tenta uma última recuperação rápida
        user_data = Database.buscar_usuario("phdantasdesousa@gmail.com")
        if user_data:
            st.session_state.user_id = str(user_data.get("_id"))
            st.session_state.user_name = user_data.get("nome")
        else:
            st.session_state.authenticated = False
            cookies["auth_token"] = ""
            cookies.save()
            st.rerun()

    # --- GERENCIAMENTO DE TEMA ---
    if 'theme_manager' not in st.session_state:
        st.session_state.theme_manager = ThemeManager()

    # --- GARANTIA DE TEMA PARA NOVOS USUÁRIOS ---
    if 'theme_colors' not in st.session_state:
        # 1. Tenta carregar do banco
        cores_do_banco = Database.carregar_preferencias()

        # 2. Se o banco estiver vazio (Novo Usuário), define o Luxury como padrão
        if not cores_do_banco:
            # Padrão Luxury: Ciano, Texto Branco, Fundo Preto, Sidebar Dark
            st.session_state.theme_colors = ("#4facfe", "#FFFFFF", "#050608", "#0d1b2a")
            # Salva para que o novo usuário já tenha isso registrado
            Database.salvar_preferencias(st.session_state.theme_colors)
        else:
            st.session_state.theme_colors = cores_do_banco

    # 3. INJEÇÃO IMEDIATA DO CSS (Evita o "flash" branco)
    if 'theme_manager' not in st.session_state:
        st.session_state.theme_manager = ThemeManager()

    st.markdown(
        st.session_state.theme_manager.get_theme_css(st.session_state.theme_colors),
        unsafe_allow_html=True
    )

    # --- ESTILO CSS CUSTOMIZADO ---
    st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        #MainMenu, footer { visibility: hidden; }
        [data-testid="stHeader"] { background: rgba(0,0,0,0) !important; color: inherit !important; }
        .block-container { padding-top: 1rem; }
        [data-testid="stSidebarContent"] .stButton button {
            width: 100%; border-radius: 8px; height: 2.4em; text-align: left;
            padding-left: 12px; margin-bottom: 4px; display: flex; align-items: center; font-size: 0.9rem; 
        }
        [data-testid="stSidebarContent"] { padding-top: 0rem !important; }
        .stSelectSlider { padding-top: 0px !important; margin-top: -5px !important; }
        hr { margin: 1em 0 !important; opacity: 0.1 !important; }
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
        mask_pagar = (df_calc['tipo'] == "Despesa") & (df_calc.get('status', '') != "🟢 Concluído")
        mask_receber = (df_calc['tipo'] == "Receita") & (df_calc.get('status', '') != "🟢 Concluído")
        pendente_pagar = df_calc[mask_pagar]['valor'].sum()
        pendente_receber = df_calc[mask_receber]['valor'].sum()
        saldo_disponivel = saldo_atual_contas
    else:
        saldo_disponivel = saldo_atual_contas
        pendente_pagar = 0.0
        pendente_receber = 0.0

    # =====================================================
    # 3. SIDEBAR (MENU)
    # =====================================================
    with st.sidebar:
        tema_atual = st.session_state.get("tema", "padrão")
        logo_path = "assets/logo_light.png" if tema_atual == "padrão" else "assets/logo_dark.png"

        if os.path.exists(logo_path):
            st.markdown("<div style='text-align: center; padding-bottom: 10px;'>", unsafe_allow_html=True)
            st.image(logo_path, width=180)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.title("💎 PlanejAI")

        if st.button("📈 Resumo Mensal"): st.session_state.pagina = "Resumo"
        if st.button("🎯 Inteligência Financeira"): st.session_state.pagina = "Inteligencia_Financeira"
        if st.button("➕ Gerenciar Lançamentos"): st.session_state.pagina = "Lançamento"
        if st.button("💰 Meus Saldos"): st.session_state.pagina = "Saldos"
        if st.button("📄 Exportar Relatórios"): st.session_state.pagina = "Exportacao"
        if st.button("🤖 IA Consultora"): st.session_state.pagina = "IA"
        if st.button("⚙️ Configurações"): st.session_state.pagina = "Config"

        st.write("---")
        # No app.py, dentro do 'with st.sidebar:'
        if st.button("🚪 Sair do Sistema"):
            # 1. Limpa o Cookie no Navegador
            cookies["auth_token"] = ""
            cookies.save()  # <--- ESSENCIAL: Grava a remoção imediatamente

            # 2. Limpa a Memória RAM do Streamlit
            st.session_state.authenticated = False
            if 'user_id' in st.session_state:
                del st.session_state.user_id

            # 3. Reinicia o App para voltar à tela de Login
            st.rerun()

        st.write("---")
        st.metric("Saldo em Contas", f"R$ {saldo_disponivel:,.2f}")
        if pendente_receber > 0: st.caption(f"🟢 **A Receber:** R$ {pendente_receber:,.2f}")
        if pendente_pagar > 0: st.caption(f"🔴 **A Pagar:** R$ {pendente_pagar:,.2f}")

        hoje = datetime.now()
        meses_restantes = 12 - hoje.month + 1
        try:
            media_disponivel_mes = (pendente_receber - pendente_pagar) / meses_restantes
        except ZeroDivisionError:
            media_disponivel_mes = 0

        if media_disponivel_mes != 0:
            st.write("")
            cor_kpi = "💰" if media_disponivel_mes > 0 else "⚠️"
            st.caption(f"{cor_kpi} **Média disponível mensal:**")
            st.markdown(f"**R$ {media_disponivel_mes:,.2f}** <small>/ mês</small>", unsafe_allow_html=True)

    # =====================================================
    # 3.5 VERIFICAÇÃO DE INTEGRIDADE (O "SEGURANÇA")
    # =====================================================
    if st.session_state.authenticated:
        if 'df' in st.session_state and not st.session_state.df.empty:
            if "user_id" in st.session_state.df.columns:
                dono_dos_dados = str(st.session_state.df["user_id"].iloc[0])
                usuario_logado = str(st.session_state.user_id)

                if dono_dos_dados != usuario_logado:
                    st.session_state.df = Database.carregar_dados()
                    st.rerun()

    # =====================================================
    # 4. ROTEAMENTO DE PÁGINAS
    # =====================================================
    df_display = st.session_state.df.copy()
    if '_id' in df_display.columns:
        df_display = df_display.drop(columns=['_id'])

    if st.session_state.pagina == "Resumo":
        resumo_mensal_page(df_display)
    elif st.session_state.pagina == "Inteligencia_Financeira":
        df_saldos_reais = Database.carregar_saldos()
        analise_categorias_page(df_display, df_saldos_reais)
    elif st.session_state.pagina == "Lançamento":
        lancamentos_page(st.session_state.df)
    elif st.session_state.pagina == "Saldos":
        from ui.saldos_page import saldos_page

        saldos_page()
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

        # --- BLOCO CLONAGEM ---
        with st.container(border=True):
            st.subheader("🔄 Clonagem Inteligente")
            col_sel, col_btn = st.columns([2, 1])
            with col_sel:
                mes_origem_str = seletor_meses_inteligente(key_suffix="config_clonagem")
            with col_btn:
                st.write(" ")
                if st.button("🚀 Executar Clonagem", type="primary", use_container_width=True):
                    # ... (lógica de clonagem mantida integralmente conforme seu código)
                    try:
                        m_o, a_o = map(int, mes_origem_str.split('/'))
                        m_d = m_o + 1 if m_o < 12 else 1
                        a_d = a_o if m_o < 12 else a_o + 1
                        df_base = st.session_state.df.copy()
                        df_base['data_vencimento'] = pd.to_datetime(df_base['data_vencimento'])
                        mask = (df_base['data_vencimento'].dt.month == m_o) & (
                                    df_base['data_vencimento'].dt.year == a_o)
                        dados_origem = df_base[mask].copy()
                        if not dados_origem.empty:
                            if '_id' in dados_origem.columns: dados_origem.drop(columns=['_id'], inplace=True)
                            dados_origem['status'] = "🟡 Pendente"


                            def rotacionar_data(dt):
                                ultimo_dia_destino = calendar.monthrange(a_d, m_d)[1]
                                dia_seguro = min(dt.day, ultimo_dia_destino)
                                return dt.replace(year=a_d, month=m_d, day=dia_seguro)


                            dados_origem['data_vencimento'] = dados_origem['data_vencimento'].apply(rotacionar_data)
                            registros_clonados = dados_origem.to_dict('records')
                            if Database.inserir_muitos(registros_clonados):
                                st.success(f"✅ Clonado para {m_d:02d}/{a_d}.")
                                st.session_state.df = Database.carregar_dados()
                                st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Erro: {e}")