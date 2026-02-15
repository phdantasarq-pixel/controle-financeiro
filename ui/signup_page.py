import streamlit as st
from services.database import Database

def signup_page():
    # Reutilizamos o CSS do login para manter a identidade
    st.markdown("""
    <style>
        [data-testid="stSidebar"], [data-testid="stHeader"] {display: none;}
        .stApp {
            background-image: linear-gradient(rgba(5, 10, 20, 0.8), rgba(5, 10, 20, 0.8)), 
                              url('https://images.unsplash.com/photo-1464802686167-b939a6910659?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80');
            background-size: cover;
            background-position: center;
        }
        .stTextInput > div > div > input {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border-radius: 8px !important;
        }
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            border: none; color: #000; font-weight: 800; height: 3.5rem; border-radius: 12px;
        }
    </style>
    """, unsafe_allow_html=True)

    col_esp, col_form, col_esp2 = st.columns([1, 1.2, 1])

    with col_form:
        st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h2 style='color:#FFFFFF; font-weight:800; margin-bottom:0px;'>Criar Conta</h2>", unsafe_allow_html=True)
            st.markdown("<p style='color:#cccccc; margin-bottom:20px;'>Junte-se à elite financeira.</p>", unsafe_allow_html=True)

            nome = st.text_input("Como podemos te chamar?", placeholder="Seu nome completo")
            email = st.text_input("E-mail", placeholder="seu@email.com")
            senha = st.text_input("Defina uma senha", type="password", placeholder="••••••••")
            confirmar = st.text_input("Confirme a senha", type="password", placeholder="••••••••")

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Finalizar Cadastro", use_container_width=True, type="primary"):
                if not nome or not email or not senha:
                    st.error("Por favor, preencha todos os campos.")
                elif senha != confirmar:
                    st.error("As senhas não coincidem.")
                else:
                    with st.spinner("Criando seu ecossistema..."):
                        sucesso, msg = Database.criar_usuario(nome, email, senha)
                        if sucesso:
                            st.success(msg)
                            st.balloons()
                            # Volta para o login após 2 segundos
                            st.session_state.auth_mode = "login"
                            st.rerun()
                        else:
                            st.error(msg)

            if st.button("Voltar para o Login", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()