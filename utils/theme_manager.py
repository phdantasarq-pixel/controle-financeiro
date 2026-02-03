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

        # Configurações de elevação e bordas
        card_shadow = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)" if is_light else "none"
        # Borda um pouco mais visível no modo claro para definir o accordion
        border_color = "#E2E8F0" if is_light else f"{primary}44"

        return f"""
        <style>
            :root {{
                --primary-color: {primary};
                --bg-color: {background};
                --text-color: {text};
                --sidebar-color: {sidebar};
            }}

            /* 1. FUNDO E TEXTO GLOBAL */
            .stApp {{
                background-color: var(--bg-color) !important;
                color: var(--text-color) !important;
            }}

            .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stMarkdown, .stApp div {{
                color: var(--text-color) !important;
            }}

            /* 2. REFINAMENTO DOS ACCORDIONS (EXPANDERS) */
            div[data-testid="stExpander"] {{
                background-color: {"#FFFFFF" if is_light else "rgba(255,255,255,0.03)"} !important;
                border: 1px solid {border_color} !important;
                border-radius: 12px !important;
                box-shadow: {card_shadow};
                margin-bottom: 1rem !important;
                transition: transform 0.2s ease, border-color 0.2s ease !important;
            }}

            /* Efeito ao passar o mouse no accordion */
            div[data-testid="stExpander"]:hover {{
                border-color: var(--primary-color) !important;
            }}

            /* Título do Accordion (Summary) */
            div[data-testid="stExpander"] summary {{
                padding: 0.5rem 1rem !important;
                color: var(--text-color) !important;
            }}

            div[data-testid="stExpander"] summary p {{
                font-weight: 600 !important;
                font-size: 1.05rem !important;
                color: var(--text-color) !important;
            }}

            /* Cor do ícone (seta) do accordion */
            div[data-testid="stExpander"] summary svg {{
                fill: var(--text-color) !important;
                transform: scale(1.2) !important;
            }}

            /* 3. INPUTS E SELECTS */
            div[data-baseweb="input"], div[data-baseweb="select"] > div {{
                background-color: {"#FFFFFF" if is_light else "rgba(255,255,255,0.05)"} !important;
                border: 1px solid {border_color} !important;
                border-radius: 8px !important;
                color: var(--text-color) !important;
            }}

            /* 4. BOTÕES (Primários e Secundários) */
            button[kind="primary"] {{
                background-color: var(--primary-color) !important;
                color: white !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
            }}

            button[kind="secondary"] {{
                background-color: {"#F1F5F9" if is_light else "rgba(255,255,255,0.05)"} !important;
                color: var(--text-color) !important;
                border: 1px solid {border_color} !important;
                border-radius: 8px !important;
            }}

            /* 5. SIDEBAR */
            section[data-testid="stSidebar"] {{
                background-color: var(--sidebar-color) !important;
                border-right: 1px solid {border_color} !important;
            }}

            /* 6. MÉTRICAS */
            div[data-testid="stMetricValue"] {{
                color: var(--primary-color) !important;
                font-weight: 700 !important;
            }}

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