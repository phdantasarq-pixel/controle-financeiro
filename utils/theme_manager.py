import streamlit as st


class ThemeManager:
    """Classe responsável por gerenciar e aplicar a identidade visual do PlanejAI (Somente Temas Escuros)."""

    def __init__(self):
        # Removido o tema 'Padrão'. Luxury agora é o líder.
        self.themes = {
            "Luxury": {
                "primary": "#4facfe",  # Azul Ciano Luxury
                "background": "#050608",  # Deep Space
                "text": "#FFFFFF",  # Branco Nítido
                "sidebar": "#0d1b2a"  # Azul Marinho Profundo
            },
            "Dark": {
                "primary": "#00FFAA",  # Verde Neon
                "background": "#0E1117",  # Grafite Streamlit
                "text": "#FAFAFA",  # Off-white
                "sidebar": "#161B22"  # Cinza Escuro
            }
        }

    def get_theme_css(self, theme_colors):
        primary, background, text, sidebar = theme_colors

        # Como removemos o claro, forçamos sempre o esquema dark
        scheme = "dark"
        field_bg = "#1a1c24"  # Fundo dos inputs mais suave
        border_color = f"{primary}66"  # Borda com transparência da cor primária

        return f"""
        <style>
            :root, html, body, .stApp {{
                color-scheme: {scheme} !important;
                background-color: {background} !important;
            }}

            /* --- MELHORIA DE NITIDEZ PLANEJAI --- */
            [data-testid="stMarkdownContainer"] p, label, span {{
                text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
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

            /* Item selecionado */
            li[role="option"][aria-selected="true"] {{
                background-color: {primary}33 !important;
                color: {text} !important;
                font-weight: 600 !important;
            }}

            /* Hover nos itens do Select */
            li[role="option"]:hover {{
                background-color: {primary} !important;
                color: #000000 !important; /* Texto preto no hover para contraste */
            }}

            /* INPUTS E CAMPOS */
            div[data-baseweb="input"], 
            div[data-baseweb="base-input"], 
            div[data-baseweb="select"] > div {{
                background-color: {field_bg} !important;
                border: 1px solid {border_color} !important;
                border-radius: 8px !important;
            }}

            input, textarea {{
                color: {text} !important;
                -webkit-text-fill-color: {text} !important;
            }}

            /* BOTÕES SECUNDÁRIOS E EXPANDERS */
            button[kind="secondary"], 
            div[data-testid="stExpander"], 
            div[data-testid="stExpander"] summary {{
                background-color: rgba(255,255,255,0.05) !important;
                color: {text} !important;
                border: 1px solid {border_color} !important;
            }}

            /* SIDEBAR PERSONALIZADA */
            [data-testid="stSidebar"] {{
                background-color: {sidebar} !important;
                border-right: 1px solid rgba(255,255,255,0.05);
            }}

            [data-testid="stSidebarContent"] * {{
                color: {text} !important;
            }}

            /* Ajuste de scrollbar para modo Dark */
            ::-webkit-scrollbar {{
                width: 8px;
            }}
            ::-webkit-scrollbar-track {{
                background: {background};
            }}
            ::-webkit-scrollbar-thumb {{
                background: {primary}44;
                border-radius: 10px;
            }}
        </style>
        """

    def sidebar_theme_selector(self):
        # Interface simplificada: apenas o que é bom
        theme_options = list(self.themes.keys())

        # Encontra o índice atual para não resetar o selectbox ao carregar
        current_bg = st.session_state.get('theme_colors', [None, None, ""])[2]
        idx = 1 if current_bg == "#0E1117" else 0

        theme_name = st.selectbox("Identidade Visual", theme_options, index=idx)
        s = self.themes[theme_name]

        with st.expander("Ajuste Fino do Especialista"):
            c1, c2 = st.columns(2)
            p = c1.color_picker("Destaque (Primária)", s["primary"])
            b = c2.color_picker("Fundo (Background)", s["background"])
            t = c1.color_picker("Leitura (Texto)", s["text"])
            si = c2.color_picker("Painel (Sidebar)", s["sidebar"])

        return (p, b, t, si)