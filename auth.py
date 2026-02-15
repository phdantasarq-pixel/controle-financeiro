import streamlit as st

def login_page():
    # --- CSS: FOCO NO TOPO E ALINHAMENTO ---
    st.markdown("""
    <style>
        [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}

        /* Fundo Espacial Real */
        .stApp {
            background-image: linear-gradient(rgba(5, 10, 20, 0.7), rgba(5, 10, 20, 0.7)), 
                              url('https://images.unsplash.com/photo-1464802686167-b939a6910659?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }

        /* Ajuste para subir o conteúdo */
        .block-container {
            padding-top: 2rem !important; /* Reduz o recuo do topo do Streamlit */
        }

        /* Container de Marketing */
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
            margin-top: 20px; /* Controle fino de altura */
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

        /* INPUTS BRANCOS */
        .stTextInput > div > div > input {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 2px solid #4facfe !important;
            border-radius: 12px !important;
            height: 3.2rem !important;
        }

        /* Botão Acessar */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            border: none;
            color: #000;
            font-weight: 800;
            height: 3.5rem;
            border-radius: 12px;
        }

        /* Botão Google */
        div.stButton > button:not([kind="primary"]) {
            background-color: rgba(255,255,255,0.05) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 12px;
            height: 3rem;
        }
    </style>
    """, unsafe_allow_html=True)

    # Reduzi de 3 <br> para apenas 1 para subir tudo
    st.markdown("<br>", unsafe_allow_html=True)

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
                <div class="feature-line">●&nbsp;&nbsp;<b>Saldo Projetado:</b>&nbsp; Controle do amanhã.</div>
                <div class="feature-line">●&nbsp;&nbsp;<b>Análise de Padrões:</b>&nbsp; IA em tempo real.</div>
                <div class="feature-line">●&nbsp;&nbsp;<b>WhatsApp Sync:</b>&nbsp; Comandos por voz/texto.</div>
                <div class="feature-line">●&nbsp;&nbsp;<b>IA de Faturas:</b>&nbsp; Insights de economia real.</div>
                <div class="feature-line">●&nbsp;&nbsp;<b>Metas Inteligentes:</b>&nbsp; Simulação de aportes.</div>
                <div class="feature-line">●&nbsp;&nbsp;<b>Consultoria:</b>&nbsp; Estratégias personalizadas.</div>
            </div>
        """, unsafe_allow_html=True)

    with col_login:
        # Adicionei um pequeno margin top para alinhar com o centro do painel de marketing
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h2 style='color:#FFFFFF; margin-bottom:5px; font-weight:800;'>Acesso</h2>", unsafe_allow_html=True)
            st.markdown("<p style='color:#cccccc; font-size:0.95rem; margin-bottom:20px;'>Entre na nova era financeira.</p>", unsafe_allow_html=True)

            email = st.text_input("Identificação", placeholder="seu@email.com", key="login_user")
            senha = st.text_input("Senha", type="password", placeholder="••••••••", key="login_pass")

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Entrar no PlanejAI", use_container_width=True, type="primary"):
                if email == "admin" and senha == "admin":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")

            if st.button("Continuar com Google", use_container_width=True, key="google_login"):
                st.toast("Conectando ao Google...")

            st.markdown("""
                <div style='text-align: center; margin-top: 20px;'>
                    <a href='#' style='color: #4facfe; text-decoration: none; font-size: 0.9rem;'>Esqueceu a senha?</a>
                    <p style='font-size: 0.9rem; margin-top: 10px; color: #888;'>
                        Novo por aqui? <a href='#' style='color: #4facfe; text-decoration: none; font-weight: bold;'>Cadastre-se</a>
                    </p>
                </div>
            """, unsafe_allow_html=True)