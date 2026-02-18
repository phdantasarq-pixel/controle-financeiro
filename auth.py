import streamlit as st
from services.database import Database


def login_page(cookies_manager): # <--- ADICIONE O ARGUMENTO AQUI

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

        .mkt-box {
            background: rgba(0, 0, 0, 0.25);
            backdrop-filter: blur(20px);
            padding: 40px;
            border-radius: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            min-height: 480px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            margin-top: 20px;
        }

        .title-hero {
            font-size: 4.2rem;
            font-weight: 900;
            color: #FFFFFF !important;
            letter-spacing: -2px;
            margin: 0;
            line-height: 1;
            text-shadow: 2px 2px 0px rgba(0,0,0,0.5), 0 0 10px rgba(79, 172, 254, 0.4);
        }

        .feature-line {
            color: #f0f0f0;
            font-size: 1.1rem;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
        }

        .stTextInput > div > div > input {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 2px solid #4facfe !important;
            border-radius: 8px !important; /* Ajustado de 0 para 8 para combinar com o sistema */
            height: 3.2rem !important;
        }

        /* Botão de Login: Forçando Largura Total e Estilo Luxury */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%) !important;
            border: none !important;
            color: #000 !important;
            font-weight: 800 !important;
            height: 3.8rem !important; /* Um pouco mais alto para destaque */
            width: 100% !important;    /* Força a largura total */
            display: block !important;  /* Garante que ele se comporte como bloco */
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
        }
        
        div[data-testid="stColumn"] > div > div > div > button:hover {
            text-decoration: underline !important;
            background-color: transparent !important;
        }
    </style>
    """, unsafe_allow_html=True)

    col_esp, col_mkt, col_login, col_esp2 = st.columns([0.4, 1.8, 1.2, 0.4])

    with col_mkt:
        st.markdown(f"""
            <div class="mkt-box">
                <div style="font-size: 0.85rem; color: #4facfe; letter-spacing: 5px; font-weight: 800; text-transform: uppercase; margin-bottom: 10px;">
                    Sistema de Inteligência Financeira
                </div>
                <h1 class="title-hero">PlanejAI</h1>
                <p style="font-size: 1.3rem; color: #FFFFFF; font-weight: 400; margin-top: 10px; margin-bottom: 30px; opacity: 0.9;">
                    Sua liberdade projetada por IA.
                </p>
                <div class="feature-line">●&nbsp;&nbsp;<b>Saldo Projetado</div>
                <div class="feature-line">●&nbsp;&nbsp;<b>Análise de Padrões</div>
                <div class="feature-line">●&nbsp;&nbsp;<b>WhatsApp Sync</div>
                <div class="feature-line">●&nbsp;&nbsp;<b>IA de Faturas</div>
                <div class="feature-line">●&nbsp;&nbsp;<b>Metas Inteligentes</div>
                <div class="feature-line">●&nbsp;&nbsp;<b>Consultoria Inteligente</div>
            </div>
        """, unsafe_allow_html=True)

    with col_login:
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h2 style='color:#FFFFFF; margin-bottom:5px; font-weight:800;'>Acesso</h2>",
                        unsafe_allow_html=True)
            st.markdown(
                "<p style='color:#cccccc; font-size:0.95rem; margin-bottom:20px;'>Entre na nova era financeira.</p>",
                unsafe_allow_html=True)

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

                        # --- CORREÇÃO DO ERRO ---
                        # Usamos o manager que veio por argumento e salvamos
                        cookies_manager["auth_token"] = "token_valido_do_ph"
                        cookies_manager.save()  # Importante para gravar no disco/browser

                        st.rerun()

                    else:
                        st.error("Credenciais inválidas.")

            # --- BOTÃO GOOGLE ---
            st.button("Continuar com Google", use_container_width=True, key="google_login")

            # --- RODAPÉ COM NAVEGAÇÃO PARA CADASTRO ---
            st.markdown("<div style='text-align: center; margin-top: 15px;'>", unsafe_allow_html=True)

            # Usamos colunas pequenas para centralizar o texto e o botão de "Cadastre-se"
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                if st.button("Ainda não tem conta? Cadastre-se", key="go_to_signup"):
                    st.session_state.auth_mode = "signup"
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)