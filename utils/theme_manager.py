import streamlit as st


class ThemeManager:
    """Classe responsável por gerenciar e aplicar a identidade visual do PlanejAI."""

    def __init__(self):
        self.themes = {
            "Padrão": {
                "primary": "#4CAF50",
                "background": "#FFFFFF",
                "text": "#1E293B",
                "sidebar": "#F8FAFC"
            },
            "Dark": {
                "primary": "#00FFAA",
                "background": "#0E1117",
                "text": "#FAFAFA",
                "sidebar": "#161B22"
            },
            "Luxury": {
                "primary": "#D4AF37",
                "background": "#121212",
                "text": "#E5E7EB",
                "sidebar": "#1C1C1C"
            }
        }

    def get_theme_css(self, theme_colors):
        primary, background, text, sidebar = theme_colors
        is_light = background.upper() in ["#FFFFFF", "#F8FAFC", "#F0F2F6", "#F1F5F9"]

        input_bg = "#FFFFFF" if is_light else "rgba(255, 255, 255, 0.05)"
        input_border = "#CBD5E1" if is_light else f"{primary}44"
        sec_button_bg = "#F1F5F9" if is_light else "rgba(255, 255, 255, 0.08)"
        card_shadow = "0 2px 4px rgba(0,0,0,0.05)" if is_light else "none"

        return f"""
        <style>
            :root {{
                --primary-color: {primary};
                --bg-color: {background};
                --text-color: {text};
            }}

            /* 1. RESET GLOBAL */
            .stApp {{
                background-color: var(--bg-color) !important;
                color: var(--text-color) !important;
            }}

            /* 2. ENTRADAS DE DADOS (INPUTS E SELECTBOX) */
            div[data-baseweb="input"], 
            div[data-baseweb="select"] > div, 
            div[data-baseweb="textarea"] textarea,
            div[data-testid="stNumberInputContainer"],
            div[data-baseweb="base-input"] {{
                background-color: {input_bg} !important;
                border: 1px solid {input_border} !important;
                border-radius: 8px !important;
            }}

            /* --- CORREÇÃO DEFINITIVA DO COMBOBOX (TEXTO SELECIONADO) --- */
            /* Ataca o texto interno que o Streamlit teima em deixar branco */
            div[data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
            div[data-baseweb="select"] div[role="button"],
            div[data-baseweb="select"] div[aria-selected="true"],
            .stSelectbox div[data-baseweb="select"] {{
                color: var(--text-color) !important;
                -webkit-text-fill-color: var(--text-color) !important;
            }}

            /* Isso ataca o valor que aparece após selecionar */
            div[data-baseweb="select"] div {{
                color: var(--text-color) !important;
            }}

            /* Forçar cor em inputs de texto e número */
            input, select, textarea {{
                color: var(--text-color) !important;
                -webkit-text-fill-color: var(--text-color) !important;
            }}

            /* 3. ACCORDIONS (MANTIDOS) */
            div[data-testid="stExpander"] {{
                background-color: {input_bg} !important;
                border: 1px solid {input_border} !important;
                border-radius: 12px !important;
                box-shadow: {card_shadow};
            }}

            div[data-testid="stExpander"] summary {{
                color: var(--text-color) !important;
                background-color: {"#F8FAFC" if is_light else "transparent"} !important;
            }}

            div[data-testid="stExpander"] summary p {{
                color: var(--text-color) !important;
                font-weight: 600 !important;
            }}

            /* 4. BOTÕES */
            button[kind="primary"], button[kind="primaryFormSubmit"] {{
                background-color: var(--primary-color) !important;
                color: white !important;
                border: none !important;
                padding: 0.5rem 2rem !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
                width: 100%;
            }}

            button[kind="secondary"] {{
                background-color: {sec_button_bg} !important;
                color: var(--text-color) !important;
                border: 1px solid {input_border} !important;
                border-radius: 8px !important;
            }}

            /* 5. SIDEBAR */
            section[data-testid="stSidebar"] {{
                background-color: {sidebar} !important;
                border-right: 1px solid {input_border} !important;
            }}

            /* 6. TEXTOS GERAIS */
            .stMarkdown p, .stApp label, div[data-testid="stMarkdownContainer"] p {{
                color: var(--text-color) !important;
            }}

            div[data-testid="stMetricValue"] {{ color: var(--primary-color) !important; font-weight: 800 !important; }}

            #MainMenu, footer, [data-testid="stHeader"] {{ visibility: hidden; }}
        </style>
        """

    def sidebar_theme_selector(self):
        st.subheader("🎨 Customização Visual")
        theme_options = list(self.themes.keys())
        theme_name = st.selectbox("Selecione o Tema", theme_options)
        s = self.themes[theme_name]
        with st.expander("Ajuste Fino (Opcional)"):
            c1, c2 = st.columns(2)
            p = c1.color_picker("Cor Primária", s["primary"])
            b = c2.color_picker("Cor de Fundo", s["background"])
            t = c1.color_picker("Cor do Texto", s["text"])
            si = c2.color_picker("Cor da Sidebar", s["sidebar"])
        return (p, b, t, si)