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

        scheme = "light" if is_light else "dark"
        # No Dark, o fundo do botão deve ser escuro e a borda visível
        button_bg = "#FFFFFF" if is_light else "rgba(255, 255, 255, 0.05)"
        border_color = "#E2E8F0" if is_light else f"{primary}88"  # Aumentei a opacidade da borda

        return f"""
        <style>
            /* 1. RESET DE ESQUEMA DO NAVEGADOR */
            :root, html, body, .stApp {{
                color-scheme: {scheme} !important;
                background-color: {background} !important;
            }}

            /* 2. O ALVO DO SEU LOG: BOTÕES SECUNDÁRIOS (ex: "Jul") */
            /* Usamos o seletor de atributo para ser mais forte que o emotion-cache */
            button[kind="secondary"] {{
                background-color: {button_bg} !important;
                color: {text} !important;
                border: 1px solid {border_color} !important;
                border-radius: 8px !important;
            }}

            button[kind="secondary"]:hover {{
                border-color: {primary} !important;
                color: {primary} !important;
                background-color: rgba(255, 255, 255, 0.1) !important;
            }}

            /* 3. EXPANDERS E CONTAINERS (O que vimos antes) */
            div[data-testid="stExpander"], 
            div[data-testid="stExpander"] summary,
            div[role="button"] {{
                background-color: {button_bg} !important;
                color: {text} !important;
                border: 1px solid {border_color} !important;
            }}

            /* 4. FORÇAR COR DO TEXTO EM TUDO */
            /* Isso garante que o texto dentro dos botões e markdowns siga o tema */
            .stApp *, [data-testid="stMarkdownContainer"] p {{
                color: {text} !important;
            }}

            /* 5. SIDEBAR */
            [data-testid="stSidebar"], [data-testid="stSidebar"] > div {{
                background-color: {sidebar} !important;
                border-right: 1px solid {border_color} !important;
            }}

            /* 6. INPUTS E CAMPOS DE SELEÇÃO */
            div[data-baseweb="input"], div[data-baseweb="select"] > div {{
                background-color: {button_bg} !important;
                border: 1px solid {border_color} !important;
            }}

            /* 7. REMOVER O HEADER DO STREAMLIT QUE PODE ESTAR BRANCO */
            header[data-testid="stHeader"] {{
                background-color: rgba(0,0,0,0) !important;
            }}

            /* Ajuste específico para ícones dentro de botões */
            [data-testid="stIconMaterial"] {{
                color: inherit !important;
            }}
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