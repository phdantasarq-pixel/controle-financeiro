import streamlit as st
import pandas as pd
from services.database import Database


def saldos_page():
    st.header("💰 Gestão de Saldos Gerais")
    st.caption(
        "Registre aqui os valores que você possui em contas ou em mãos. Isso servirá de contexto para seu planejamento.")

    # Carrega os dados específicos de saldos
    if "df_saldos" not in st.session_state:
        st.session_state.df_saldos = Database.carregar_saldos()

    df_saldos = st.session_state.df_saldos

    # --- EDITOR DE SALDOS ---
    st.subheader("🏦 Suas Contas e Reservas")

    # Adicionar nova conta
    with st.expander("➕ Adicionar Nova Conta/Local"):
        c1, c2 = st.columns([2, 1])
        nova_conta = c1.text_input("Nome (ex: Nubank, Carteira, Cofre)")
        novo_valor = c2.number_input("Valor Atual", min_value=0.0, step=50.0)
        if st.button("Registrar"):
            if nova_conta:
                novo_item = pd.DataFrame([{"conta": nova_conta, "valor": novo_valor}])
                st.session_state.df_saldos = pd.concat([st.session_state.df_saldos, novo_item], ignore_index=True)
                Database.salvar_saldos(st.session_state.df_saldos)
                st.rerun()

    if not df_saldos.empty:
        df_editado = st.data_editor(
            df_saldos,
            use_container_width=True,
            hide_index=True,
            column_config={
                "conta": st.column_config.TextColumn("Instituição/Local", help="Onde o dinheiro está?"),
                "valor": st.column_config.NumberColumn("Valor Disponível", format="R$ %.2f")
            },
            key="editor_saldos"
        )

        # Autosave para os saldos
        if not df_editado.equals(df_saldos):
            st.session_state.df_saldos = df_editado
            Database.salvar_saldos(df_editado)
            st.toast("Saldos atualizados!", icon="💰")

        total = df_editado['valor'].sum()
        st.info(f"**Total Disponível:** R$ {total:,.2f}")
    else:
        st.info("Nenhuma conta registrada ainda.")