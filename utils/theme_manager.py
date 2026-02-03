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
        field_bg = "#FFFFFF" if is_light else "#262730"
        border_color = "#E2E8F0" if is_light else f"{primary}66"

        return f"""
        <style>
            :root, html, body, .stApp {{
                color-scheme: {scheme} !important;
                background-color: {background} !important;
            }}

            /* COMBOBOX / SELECTBOX */
            div[data-baseweb="popover"], 
            div[role="listbox"], 
            ul[role="listbox"] {{
                background-color: {field_bg} !important;
                border: 1px solid {border_color} !important;
            }}

            /* Itens da lista */
            li[role="option"] {{
                color: {text} !important;
            }}

            li[role="option"] [data-testid="stTooltipHoverTarget"] div {{
                color: {text} !important;
                -webkit-text-fill-color: {text} !important;
            }}

            /* Item selecionado */
            li[role="option"][aria-selected="true"] {{
                background-color: {primary}33 !important;
                color: {text} !important;
                font-weight: 600 !important;
            }}

            /* Hover */
            li[role="option"]:hover {{
                background-color: {primary} !important;
                color: #FFFFFF !important;
            }}

            li[role="option"]:hover [data-testid="stTooltipHoverTarget"] div {{
                color: #FFFFFF !important;
                -webkit-text-fill-color: #FFFFFF !important;
            }}

            /* Texto exibido dentro do campo do select */
            div[data-baseweb="select"] div[role="combobox"] {{
                color: {text} !important;
                -webkit-text-fill-color: {text} !important;
            }}

            div[data-baseweb="select"] div[role="combobox"] * {{
                color: {text} !important;
                -webkit-text-fill-color: {text} !important;
            }}

            /* INPUTS */
            div[data-baseweb="input"], 
            div[data-baseweb="base-input"], 
            div[data-baseweb="select"] > div {{
                background-color: {field_bg} !important;
                border: 1px solid {border_color} !important;
            }}

            input, textarea {{
                color: {text} !important;
                -webkit-text-fill-color: {text} !important;
            }}

            /* BOTÕES E EXPANDERS */
            button[kind="secondary"], 
            div[data-testid="stExpander"], 
            div[data-testid="stExpander"] summary {{
                background-color: {field_bg} !important;
                color: {text} !important;
                border: 1px solid {border_color} !important;
            }}

            /* TEXTO UNIVERSAL */
            .stApp *, 
            [data-testid="stMarkdownContainer"] p, 
            label,
            div[data-testid="stTooltipHoverTarget"] div {{
                color: {text} !important;
                -webkit-text-fill-color: {text} !important;
            }}

            /* SIDEBAR */
            [data-testid="stSidebar"] {{
                background-color: {sidebar} !important;
            }}

            [data-testid="stSidebar"] * {{
                color: {text} !important;
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
