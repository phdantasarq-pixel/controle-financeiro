import streamlit as st
from services.database import Database


def login_page(cookie_manager):

    # --- CSS: MANTIDO INTEGRALMENTE (Luxury Space) ---
    st.markdown("""
    <style>
        [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}

        .stApp {
            background-image: linear-gradient(rgba(5, 10, 20, 0.7), rgba(5, 10, 20, 0.7)), 
                              url('https://images.unsplash.com/photo-1464802686167-b939a6910659?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }

        .block-container { padding-top: 2rem !important; }

        .stTextInput > div > div > input {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 2px solid #4facfe !important;
            border-radius: 8px !important;
            height: 3.2rem !important;
        }

        /* Botão de Login: Forçando Largura Total e Estilo Luxury */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%) !important;
            border: none !important;
            color: #000 !important;
            font-weight: 800 !important;
            height: 3.8rem !important;
            width: 100% !important;
            display: block !important;
            border-radius: 12px !important;
            margin-top: 20px !important;
            font-size: 1.1rem !important;
            box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3) !important;
            transition: all 0.3s ease !important;
        }

        /* Efeito de hover para ficar bem profissional */
        div.stButton > button[kind="primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(79, 172, 254, 0.5) !important;
        }

        div.stButton > button:not([kind="primary"]) {
            background-color: rgba(255,255,255,0.05) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 12px;
            height: 3rem;
            width: 100% !important;
        }

        /* Transforma o botão de navegação em um link fake elegante */
        div[data-testid="stColumn"] > div > div > div > button:not([kind="primary"]) {
            background-color: transparent !important;
            border: none !important;
            color: #4facfe !important;
            text-decoration: none !important;
            font-size: 0.9rem !important;
            height: auto !important;
            padding: 0 !important;
            box-shadow: none !important;
        }

        div[data-testid="stColumn"] > div > div > div > button:hover {
            text-decoration: underline !important;
            background-color: transparent !important;
        }

        /* Estiliza o container central para parecer um card moderno (Glassmorphism) */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(0, 0, 0, 0.35) !important;
            backdrop-filter: blur(20px) !important;
            border-radius: 24px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            padding: 25px !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Layout de 3 colunas (Centraliza no desktop e força 100% no mobile)
    col_left, col_center, col_right = st.columns([1, 1.5, 1])

    with col_center:
        # Espaçador superior para não ficar colado no topo
        st.markdown("<div style='margin-top: 6vh;'></div>", unsafe_allow_html=True)

        # Quadrado principal único
        with st.container(border=True):

            # Título do App dentro do Card
            st.markdown("""
                <div style="text-align: center; margin-bottom: 30px;">
                    <div style="font-size: 0.75rem; color: #4facfe; letter-spacing: 4px; font-weight: 800; text-transform: uppercase; margin-bottom: 5px;">
                        Sistema de Inteligência Financeira
                    </div>
                    <h1 style="font-size: 3rem; font-weight: 900; color: #FFFFFF; margin: 0; line-height: 1; text-shadow: 2px 2px 0px rgba(0,0,0,0.5), 0 0 10px rgba(79, 172, 254, 0.4);">
                        PlanejAI
                    </h1>
                </div>
            """, unsafe_allow_html=True)

            # Cabeçalho de Acesso
            st.markdown("<h2 style='color:#FFFFFF; margin-bottom:5px; font-weight:800; text-align:center;'>Acesso</h2>",
                        unsafe_allow_html=True)
            st.markdown(
                "<p style='color:#cccccc; font-size:0.95rem; margin-bottom:20px; text-align:center;'>Entre na nova era financeira.</p>",
                unsafe_allow_html=True)

            # Campos de Entrada
            email_input = st.text_input("Identificação", placeholder="seu@email.com", key="login_user")
            senha_input = st.text_input("Senha", type="password", placeholder="••••••••", key="login_pass")

            st.markdown("<br>", unsafe_allow_html=True)

            # --- BOTÃO DE LOGIN REAL ---
            if st.button("Entrar no PlanejAI", use_container_width=True, type="primary"):
                with st.spinner("Autenticando..."):
                    user_data = Database.buscar_usuario(email_input)
                    if user_data and user_data.get("senha") == senha_input:
                        st.session_state.authenticated = True
                        st.session_state.user_id = str(user_data.get("_id"))
                        # FORÇA a limpeza e recarga dos dados do NOVO usuário
                        st.session_state.df = Database.carregar_dados()

                        st.session_state.user_name = user_data.get("nome", "Usuário")

                        if cookie_manager:
                            cookie_manager.set("auth_token", email_input)

                        st.rerun()

                    else:
                        st.error("Credenciais inválidas.")

            # --- BOTÃO GOOGLE ---
            st.button("Continuar com Google", use_container_width=True, key="google_login")

            # --- RODAPÉ COM NAVEGAÇÃO PARA CADASTRO ---
            st.write("")  # Dá um pequeno espaço visual

            c1, c2, c3 = st.columns([0.5, 2, 0.5])
            with c2:
                if st.button("Ainda não tem conta? Cadastre-se", key="go_to_signup"):
                    st.session_state.auth_mode = "signup"
                    st.rerun()
