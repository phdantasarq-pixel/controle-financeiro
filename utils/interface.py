import streamlit as st


class ThemeManager:
    """Classe responsável por gerenciar e aplicar a identidade visual do PlanejAI."""

    def __init__(self):
        self.themes = {
            "Padrão PlanejAI": {
                "primary": "#4CAF50",
                "background": "#FFFFFF",
                "text": "#31333F",
                "sidebar": "#F0F2F6"
            },
            "Dark Mode": {
                "primary": "#00FFAA",
                "background": "#0E1117",
                "text": "#FAFAFA",
                "sidebar": "#262730"
            },
            "Ocean Blue": {
                "primary": "#0077B6",
                "background": "#CAF0F8",
                "text": "#03045E",
                "sidebar": "#90E0EF"
            },
            "Luxury Gold": {
                "primary": "#D4AF37",
                "background": "#1A1A1A",
                "text": "#E6E6E6",
                "sidebar": "#2D2D2D"
            }
        }

    def get_theme_css(self, theme_colors):
        primary, background, text, sidebar = theme_colors

        # Detecção de brilho para contraste inteligente
        is_light = background.upper() in ["#FFFFFF", "#CAF0F8", "#F0F2F6", "#E9F5EB"]
        widget_bg = "rgba(0,0,0,0.05)" if is_light else "rgba(255,255,255,0.05)"
        border_color = f"{primary}44"  # Cor primária com ~25% de opacidade

        return f"""
        <style>
            /* Definição de Variáveis para uso global */
            :root {{
                --primary-color: {primary};
                --bg-color: {background};
                --text-color: {text};
                --sidebar-color: {sidebar};
                --widget-bg: {widget_bg};
                --border-color: {border_color};
            }}

            /* Configurações Globais */
            .stApp {{
                background-color: var(--bg-color);
                color: var(--text-color);
            }}

            [data-testid="stSidebar"] {{
                background-color: var(--sidebar-color) !important;
            }}

            /* Ajuste de Tipografia */
            h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {{
                color: var(--text-color) !important;
            }}

            /* --- WIDGETS DE ENTRADA --- */
            .stTextInput input, .stSelectbox div, .stDateInput div, .stNumberInput input {{
                background-color: var(--widget-bg) !important;
                color: var(--text-color) !important;
                border-radius: 8px !important;
                border: 1px solid var(--border-color) !important;
            }}

            /* --- BOTÕES SECUNDÁRIOS --- */
            button[kind="secondary"] {{
                background-color: var(--widget-bg) !important;
                color: var(--text-color) !important;
                border: 1px solid var(--border-color) !important;
                transition: all 0.3s ease;
            }}

            button[kind="secondary"]:hover {{
                border-color: var(--primary-color) !important;
                color: var(--primary-color) !important;
                background-color: {primary}11 !important;
            }}

            /* --- BOTÕES PRIMÁRIOS --- */
            div.stButton > button[kind="primary"] {{
                background-color: var(--primary-color) !important;
                color: {"#FFFFFF" if not is_light else "#000000"} !important;
                border-radius: 8px !important;
                border: none !important;
                font-weight: 600 !important;
                width: 100%;
            }}

            /* --- [RESOLUÇÃO] AJUSTE DOS ACCORDIONS (st.expander) --- */
            /* Remove a borda padrão e o estilo de foco do elemento details nativo */
            [data-testid="stExpander"] {{
                background-color: var(--widget-bg) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: 8px !important;
                overflow: hidden !important;
                box-shadow: none !important;
            }}

            /* Estiliza o cabeçalho (clickable summary) */
            [data-testid="stExpander"] summary {{
                background-color: transparent !important;
                color: var(--text-color) !important;
                padding: 12px 16px !important;
                border-bottom: none !important;
                transition: background 0.3s;
            }}

            [data-testid="stExpander"] summary:hover {{
                background-color: rgba(255,255,255,0.05) !important;
            }}

            /* Força a cor do texto/ícone dentro do summary */
            [data-testid="stExpander"] summary span, 
            [data-testid="stExpander"] summary p {{
                color: var(--text-color) !important;
                font-weight: 600 !important;
            }}

            /* Cor do ícone de seta */
            [data-testid="stExpander"] summary svg {{
                fill: var(--primary-color) !important;
            }}

            /* Estiliza o conteúdo interno (o bloco vertical que surge ao abrir) */
            [data-testid="stExpander"] [data-testid="stVerticalBlock"] {{
                padding: 15px !important;
                background-color: transparent !important;
                border-top: 1px solid var(--border-color) !important;
            }}

            /* --- [H8.1] CARDS DE SALDO E MÉTRICAS --- */
            [data-testid="stMetric"] {{
                background-color: var(--widget-bg);
                padding: 15px;
                border-radius: 10px;
                border-left: 5px solid var(--primary-color);
            }}

            [data-testid="stMetricValue"] {{
                color: var(--text-color) !important;
                font-weight: bold !important;
            }}

            /* --- TABELAS E DATAFRAMES --- */
            [data-testid="stTable"], [data-testid="stDataFrame"] {{
                background-color: var(--bg-color);
                color: var(--text-color);
            }}

            /* Limpeza de Interface */
            #MainMenu {{visibility: hidden;}}
            footer {{visibility: hidden;}}
            [data-testid="stHeader"] {{background: rgba(0,0,0,0);}}
        </style>
        """

    def sidebar_theme_selector(self):
        st.subheader("🎨 Customização Visual")
        mode = st.radio("Modo de Seleção", ["Presets", "Customizado"], horizontal=True)

        if mode == "Presets":
            theme_name = st.selectbox("Escolha um Tema", list(self.themes.keys()))
            selected = self.themes[theme_name]
            colors = (selected["primary"], selected["background"], selected["text"], selected["sidebar"])
        else:
            c1 = st.color_picker("Cor Primária", "#4CAF50")
            c2 = st.color_picker("Fundo da Tela", "#FFFFFF")
            c3 = st.color_picker("Cor do Texto", "#31333F")
            c4 = st.color_picker("Cor da Sidebar", "#F0F2F6")
            colors = (c1, c2, c3, c4)

        return colors