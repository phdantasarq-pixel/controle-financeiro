import streamlit as st
import pandas as pd
from services.database import Database

def saldos_page():
    # --- CABEÇALHO MODERNIZADO (PADRÃO COCKPIT RESUMO) ---
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;800&display=swap');

            .main-header {
                font-family: 'Inter', sans-serif;
                padding: 20px 0 10px 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                margin-bottom: 30px;
            }

            .title-main {
                font-size: 2.2rem;
                font-weight: 800;
                letter-spacing: -1px;
                background: linear-gradient(90deg, #FFFFFF 0%, #A0A0A0 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0px;
                text-transform: uppercase;
            }

            .subtitle-main {
                font-size: 0.85rem;
                font-weight: 300;
                color: #3498db;
                letter-spacing: 3px;
                text-transform: uppercase;
                opacity: 0.9;
            }

            .accent-line {
                width: 50px;
                height: 4px;
                background: #3498db;
                border-radius: 10px;
                margin-top: 15px;
            }

            /* Estilo dos Cards Glassmorphism */
            .card-modern {
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.01));
                padding: 20px; 
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1); 
                backdrop-filter: blur(10px);
                margin-bottom: 15px; 
                color: white;
                border-top: 4px solid #3498db;
            }
            .label { font-size: 0.75rem; text-transform: uppercase; opacity: 0.8; letter-spacing: 1px; }
            .value { font-size: 1.8rem; font-weight: 800; margin: 5px 0; color: #fff; }
        </style>

        <div class="main-header">
            <div class="subtitle-main">Cockpit de Liquidez</div>
            <div class="title-main">Gestão de Saldos</div>
            <div class="subtitle-main" style="color: rgba(255,255,255,0.4); letter-spacing: 1px; margin-top: 5px;">
                PlanejAI <span style="color: #3498db; font-weight: bold;">v8.1</span>
            </div>
            <div class="accent-line"></div>
        </div>
    """, unsafe_allow_html=True)

    # Carregar dados
    if "df_saldos" not in st.session_state:
        st.session_state.df_saldos = Database.carregar_saldos()

    df_saldos = st.session_state.df_saldos.copy()
    total = df_saldos['valor'].sum() if not df_saldos.empty else 0.0

    # --- CARD DE PATRIMÔNIO (ESTILO RESUMO) ---
    st.markdown(f"""
        <div class="card-modern">
            <div class="label">Patrimônio Líquido Disponível 💰</div>
            <div class="value">R$ {total:,.2f}</div>
            <div style="font-size: 0.8rem; color: #2ecc71; font-weight: 600;">
                ● Live Update (Tempo Real)
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- CONTEÚDO ---
    col_lista, col_add = st.columns([1.6, 1.4], gap="large")

    with col_lista:
        st.markdown('<p class="subtitle-main" style="margin-bottom:15px; font-size:1rem;">🏦 Portfólio de Contas</p>', unsafe_allow_html=True)
        if not df_saldos.empty:
            df_saldos["🗑️"] = False
            df_editado = st.data_editor(
                df_saldos,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "🗑️": st.column_config.CheckboxColumn("Excluir", width="small"),
                    "conta": st.column_config.TextColumn("Instituição / Ativo"),
                    "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")
                },
                key="editor_saldos_luxury_v8"
            )

            # Lógica de Salvamento/Exclusão
            if not df_editado.drop(columns=["🗑️"]).equals(st.session_state.df_saldos):
                if df_editado["🗑️"].any():
                    if st.button("Confirmar Exclusão de Ativos", type="primary", use_container_width=True):
                        st.session_state.df_saldos = df_editado[df_editado["🗑️"] == False].drop(columns=["🗑️"])
                        Database.salvar_saldos(st.session_state.df_saldos)
                        st.rerun()
                else:
                    st.session_state.df_saldos = df_editado.drop(columns=["🗑️"])
                    Database.salvar_saldos(st.session_state.df_saldos)
                    st.toast("Patrimônio atualizado!", icon="💰")
                    st.rerun()
        else:
            st.info("Nenhuma conta registrada no cockpit.")

    with col_add:
        st.markdown('<p class="subtitle-main" style="margin-bottom:15px; font-size:1rem; color: #3498db;">➕ Novo Registro</p>', unsafe_allow_html=True)
        with st.container(border=True):
            n_conta = st.text_input("Instituição / Ativo", placeholder="Ex: Bitcoin, Nubank...")
            n_valor = st.number_input("Saldo Atual", min_value=0.0, step=100.0, format="%.2f")

            if st.button("Acoplar ao Patrimônio", use_container_width=True, type="primary"):
                if n_conta:
                    nova_linha = pd.DataFrame([{"conta": n_conta, "valor": n_valor}])
                    st.session_state.df_saldos = pd.concat([st.session_state.df_saldos, nova_linha], ignore_index=True)
                    Database.salvar_saldos(st.session_state.df_saldos)
                    st.toast(f"{n_conta} integrado com sucesso!")
                    st.rerun()