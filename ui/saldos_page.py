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
                padding: 15px 0 10px 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                margin-bottom: 25px;
            }

            .title-main {
                font-size: 2.2rem;
                font-weight: 800;
                letter-spacing: -1px;
                color: #ffffff !important;
                margin-bottom: 0px;
                text-transform: uppercase;
            }

            .subtitle-main {
                font-size: 0.85rem;
                font-weight: 600;
                color: #38bdf8 !important;
                letter-spacing: 2px;
                text-transform: uppercase;
            }

            .accent-line {
                width: 50px;
                height: 4px;
                background: #38bdf8;
                border-radius: 10px;
                margin-top: 10px;
            }

            /* Estilo dos Cards Glassmorphism Alto Contraste */
            .card-modern {
                background: #151d2e;
                padding: 22px; 
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.12); 
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
                margin-bottom: 20px; 
                color: #ffffff;
                border-top: 4px solid #38bdf8;
            }
            .label { font-size: 0.78rem; text-transform: uppercase; color: #cbd5e1; letter-spacing: 1px; font-weight: 600; }
            .value { font-size: 1.8rem; font-weight: 800; margin: 8px 0; color: #ffffff !important; }
        </style>

        <div class="main-header">
            <div class="subtitle-main">Cockpit de Liquidez</div>
            <div class="title-main">Gestão de Saldos</div>
            <div class="subtitle-main" style="color: #94a3b8 !important; letter-spacing: 1px; margin-top: 4px;">
                PlanejAI <span style="color: #38bdf8; font-weight: bold;">v1.0</span>
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
            <div style="font-size: 0.85rem; color: #4ade80; font-weight: 700;">
                ● Live Update (Tempo Real)
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- CONTEÚDO ---
    col_lista, col_add = st.columns([1.6, 1.4], gap="large")

    with col_lista:
        st.markdown('<p class="subtitle-main" style="margin-bottom:15px; font-size:1rem; color: #ffffff !important;">🏦 Portfólio de Contas</p>',
                    unsafe_allow_html=True)
        if not df_saldos.empty:
            # Adicionando índice original para garantir exclusão precisa
            df_saldos["original_index"] = df_saldos.index
            df_saldos["🗑️"] = False

            # --- FORMULÁRIO DE GESTÃO (PADRÃO LANÇAMENTOS) ---
            with st.form(key="form_saldos_v8"):
                df_editado = st.data_editor(
                    df_saldos[["conta", "valor", "🗑️", "original_index"]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "🗑️": st.column_config.CheckboxColumn("🗑️", width="small", default=False),
                        "conta": st.column_config.TextColumn("Instituição / Ativo"),
                        "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                        "original_index": None  # Esconde o índice técnico
                    },
                    key="editor_saldos_luxury_v8"
                )

                if st.form_submit_button("💾 Salvar Alterações no Patrimônio", use_container_width=True, type="primary"):
                    # 1. Identificar itens para exclusão
                    indices_para_excluir = df_editado[df_editado["🗑️"] == True]["original_index"].tolist()

                    # 2. Atualizar o DataFrame do session_state
                    novo_df = df_editado[df_editado["🗑️"] == False].drop(columns=["🗑️", "original_index"])

                    st.session_state.df_saldos = novo_df
                    Database.salvar_saldos(st.session_state.df_saldos)

                    if indices_para_excluir:
                        st.toast(f"{len(indices_para_excluir)} ativo(s) removido(s)!", icon="🗑️")
                    else:
                        st.toast("Patrimônio atualizado!", icon="💰")

                    st.rerun()
        else:
            st.info("Nenhuma conta registrada no cockpit.")

    with col_add:
        st.markdown(
            '<p class="subtitle-main" style="margin-bottom:15px; font-size:1rem; color: #ffffff !important;">➕ Novo Registro</p>',
            unsafe_allow_html=True)
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
                else:
                    st.error("Informe o nome da instituição ou ativo.")
