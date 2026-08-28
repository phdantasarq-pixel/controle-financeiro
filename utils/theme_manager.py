import streamlit as st


class ThemeManager:
    """Classe responsável por gerenciar e aplicar a identidade visual do PlanejAI (Temas Escuros de Alto Contraste)."""

    def __init__(self):
        self.themes = {
            "Luxury (Alto Contraste)": {
                "primary": "#38bdf8",  # Azul Ciano Vibrante
                "background": "#0b0f19",  # Dark Slate Profundo
                "text": "#ffffff",  # Branco Puro
                "sidebar": "#0f172a"  # Azul Marinho Escuro
            },
            "Dark Grafite": {
                "primary": "#00ffaa",  # Verde Neon
                "background": "#0e1117",  # Grafite Escuro
                "text": "#ffffff",  # Branco Puro
                "sidebar": "#161b22"  # Cinza Escuro
            }
        }

    def get_theme_css(self, theme_colors):
        if not theme_colors or len(theme_colors) < 4:
            theme_colors = ("#38bdf8", "#0b0f19", "#ffffff", "#0f172a")

        primary, background, text, sidebar = theme_colors

        # Sanitize / normalização de segurança para contraste garantido
        # Se por acaso o texto estiver escuro ou o fundo estiver claro, forçamos alto contraste
        if text.lower() in ["#050608", "#000000", "#0e1117", "#111827", "#1a1a1a"] or text.lower().startswith("#0") or text.lower().startswith("#1"):
            text = "#ffffff"
        if background.lower() in ["#ffffff", "#fafafa", "#f0f2f6", "#fff"] or background.lower().startswith("#f") or background.lower().startswith("#e"):
            background = "#0b0f19"

        field_bg = "#1e293b"  # Fundo dos campos e cards
        card_bg = "#151d2e"
        border_color = "rgba(255, 255, 255, 0.15)"
        border_primary = f"{primary}88"

        return f"""
        <style>
            /* ===================================================
               PLANEJAI - TEMA ESCURO DE ALTO CONTRASTE
               =================================================== */

            :root, html, body, .stApp {{
                color-scheme: dark !important;
                background-color: {background} !important;
                color: {text} !important;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            }}

            /* --- TIPOGRAFIA GLOBAL DE ALTO CONTRASTE --- */
            h1, h2, h3, h4, h5, h6 {{
                color: #ffffff !important;
                font-weight: 700 !important;
                letter-spacing: -0.5px !important;
            }}

            p, span, div, li {{
                color: #f1f5f9;
            }}

            /* Labels de campos e formulários */
            label, [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label, [data-testid="stWidgetLabel"] span {{
                color: #f8fafc !important;
                font-weight: 600 !important;
                font-size: 0.95rem !important;
                opacity: 1 !important;
            }}

            /* Captions e textos secundários */
            .stCaption, [data-testid="stCaptionContainer"] p {{
                color: #94a3b8 !important;
                font-size: 0.85rem !important;
            }}

            /* --- INPUTS, TEXTAREAS E NÚMEROS --- */
            div[data-baseweb="input"], 
            div[data-baseweb="base-input"] {{
                background-color: {field_bg} !important;
                border: 1px solid {border_color} !important;
                border-radius: 8px !important;
            }}

            div[data-baseweb="input"]:focus-within, 
            div[data-baseweb="base-input"]:focus-within {{
                border-color: {primary} !important;
                box-shadow: 0 0 0 1px {primary} !important;
            }}

            input, textarea {{
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
                background-color: transparent !important;
                font-weight: 500 !important;
                font-size: 0.95rem !important;
            }}

            input::placeholder, textarea::placeholder {{
                color: #94a3b8 !important;
                -webkit-text-fill-color: #94a3b8 !important;
                opacity: 1 !important;
            }}

            /* --- SELECTBOX / COMBOBOX / POPOVERS --- */
            div[data-baseweb="select"] > div {{
                background-color: {field_bg} !important;
                border: 1px solid {border_color} !important;
                border-radius: 8px !important;
                color: #ffffff !important;
            }}

            div[data-baseweb="select"] span,
            div[data-baseweb="select"] div {{
                color: #ffffff !important;
                font-weight: 500 !important;
            }}

            div[data-baseweb="popover"], 
            div[role="listbox"], 
            ul[role="listbox"] {{
                background-color: {field_bg} !important;
                border: 1px solid {border_primary} !important;
                border-radius: 8px !important;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.6) !important;
            }}

            li[role="option"] {{
                color: #f8fafc !important;
                font-weight: 500 !important;
                padding: 10px 14px !important;
            }}

            li[role="option"][aria-selected="true"] {{
                background-color: rgba(56, 189, 248, 0.2) !important;
                color: {primary} !important;
                font-weight: 700 !important;
            }}

            li[role="option"]:hover {{
                background-color: {primary} !important;
                color: #0b0f19 !important;
                font-weight: 700 !important;
            }}

            /* --- CARDS E CONTAINERS COM BORDA --- */
            [data-testid="stVerticalBlockBorderWrapper"] {{
                background-color: {card_bg} !important;
                border: 1px solid {border_color} !important;
                border-radius: 16px !important;
                padding: 18px !important;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
            }}

            div[data-testid="stForm"] {{
                background-color: {card_bg} !important;
                border: 1px solid {border_color} !important;
                border-radius: 16px !important;
                padding: 20px !important;
            }}

            /* --- EXPANDERS --- */
            div[data-testid="stExpander"] {{
                background-color: {card_bg} !important;
                border: 1px solid {border_color} !important;
                border-radius: 12px !important;
            }}

            div[data-testid="stExpander"] summary {{
                color: #ffffff !important;
            }}

            div[data-testid="stExpander"] summary p,
            div[data-testid="stExpander"] summary span {{
                color: #ffffff !important;
                font-weight: 600 !important;
            }}

            /* --- TABS --- */
            button[data-baseweb="tab"] {{
                color: #94a3b8 !important;
                font-weight: 600 !important;
                font-size: 0.95rem !important;
                background-color: transparent !important;
                padding: 10px 18px !important;
            }}

            button[data-baseweb="tab"]:hover {{
                color: #ffffff !important;
            }}

            button[data-baseweb="tab"][aria-selected="true"] {{
                color: {primary} !important;
                border-bottom: 2px solid {primary} !important;
                font-weight: 700 !important;
            }}

            /* --- MÉTRICAS --- */
            [data-testid="stMetricValue"] {{
                color: #ffffff !important;
                font-weight: 800 !important;
            }}

            [data-testid="stMetricLabel"] p,
            [data-testid="stMetricLabel"] label {{
                color: #94a3b8 !important;
                font-weight: 600 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.5px !important;
            }}

            /* --- BOTÕES --- */
            button[kind="primary"] {{
                background: linear-gradient(135deg, {primary} 0%, #0284c7 100%) !important;
                color: #0b0f19 !important;
                font-weight: 700 !important;
                border: none !important;
                border-radius: 8px !important;
            }}

            button[kind="secondary"] {{
                background-color: {field_bg} !important;
                color: #ffffff !important;
                border: 1px solid {border_color} !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
            }}

            button[kind="secondary"]:hover {{
                border-color: {primary} !important;
                color: {primary} !important;
            }}

            /* --- SIDEBAR --- */
            [data-testid="stSidebar"] {{
                background-color: {sidebar} !important;
                border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
            }}

            [data-testid="stSidebarContent"] p,
            [data-testid="stSidebarContent"] span,
            [data-testid="stSidebarContent"] label {{
                color: #f8fafc !important;
            }}

            [data-testid="stSidebarContent"] .stButton button {{
                background-color: rgba(255, 255, 255, 0.04) !important;
                color: #f1f5f9 !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                font-weight: 600 !important;
            }}

            [data-testid="stSidebarContent"] .stButton button:hover {{
                background-color: rgba(56, 189, 248, 0.15) !important;
                border-color: {primary} !important;
                color: {primary} !important;
            }}

            /* --- DATA EDITOR / TABELAS --- */
            [data-testid="stDataFrame"], [data-testid="stDataEditor"] {{
                background-color: {card_bg} !important;
                border-radius: 12px !important;
            }}

            /* --- ALERTAS E TOASTS --- */
            div[data-testid="stAlert"] {{
                background-color: rgba(15, 23, 42, 0.9) !important;
                border: 1px solid {border_color} !important;
                color: #ffffff !important;
                border-radius: 10px !important;
            }}

            /* --- SCROLLBAR --- */
            ::-webkit-scrollbar {{
                width: 8px;
                height: 8px;
            }}
            ::-webkit-scrollbar-track {{
                background: {background};
            }}
            ::-webkit-scrollbar-thumb {{
                background: {field_bg};
                border-radius: 4px;
                border: 1px solid {border_color};
            }}
            ::-webkit-scrollbar-thumb:hover {{
                background: {primary}88;
            }}
        </style>
        """

    def sidebar_theme_selector(self):
        theme_options = list(self.themes.keys())

        current_bg = st.session_state.get('theme_colors', [None, ""])[1]
        idx = 1 if current_bg == "#0e1117" else 0

        theme_name = st.selectbox("Identidade Visual", theme_options, index=idx)
        s = self.themes[theme_name]

        with st.expander("Ajuste Fino do Especialista"):
            c1, c2 = st.columns(2)
            p = c1.color_picker("Destaque (Primária)", s["primary"])
            b = c2.color_picker("Fundo (Background)", s["background"])
            t = c1.color_picker("Leitura (Texto)", s["text"])
            si = c2.color_picker("Painel (Sidebar)", s["sidebar"])

        return (p, b, t, si)
