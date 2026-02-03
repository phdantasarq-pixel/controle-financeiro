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

    # Criamos uma cópia para trabalhar na interface
    df_saldos = st.session_state.df_saldos.copy()

    # --- ADICIONAR NOVA CONTA ---
    with st.expander("➕ Adicionar Nova Conta/Local", expanded=df_saldos.empty):
        c1, c2 = st.columns([2, 1])
        nova_conta = c1.text_input("Nome (ex: Nubank, Carteira, Cofre)")
        novo_valor = c2.number_input("Valor Atual", min_value=0.0, step=50.0, format="%.2f")
        if st.button("Registrar"):
            if nova_conta:
                novo_item = pd.DataFrame([{"conta": nova_conta, "valor": novo_valor}])
                st.session_state.df_saldos = pd.concat([st.session_state.df_saldos, novo_item], ignore_index=True)
                Database.salvar_saldos(st.session_state.df_saldos)
                st.rerun()

    # --- EDITOR DE SALDOS ---
    st.subheader("🏦 Suas Contas e Reservas")

    if not df_saldos.empty:
        # Adiciona coluna de lixeira temporária para o editor
        df_saldos["🗑️"] = False

        df_editado = st.data_editor(
            df_saldos,
            use_container_width=True,
            hide_index=True,
            column_config={
                "🗑️": st.column_config.CheckboxColumn("Excluir", default=False),
                "conta": st.column_config.TextColumn("Instituição/Local", help="Onde o dinheiro está?"),
                "valor": st.column_config.NumberColumn("Valor Disponível", format="R$ %.2f")
            },
            key="editor_saldos"
        )

        # --- LÓGICA DE EXCLUSÃO ---
        indices_para_excluir = df_editado[df_editado["🗑️"] == True].index.tolist()

        if indices_para_excluir:
            if st.button(f"🗑️ Remover {len(indices_para_excluir)} selecionado(s)", type="secondary"):
                # Remove as linhas do DataFrame original no session_state
                st.session_state.df_saldos = st.session_state.df_saldos.drop(indices_para_excluir).reset_index(
                    drop=True)
                Database.salvar_saldos(st.session_state.df_saldos)
                st.rerun()

        # --- LÓGICA DE AUTOSAVE (Apenas se não houver marcação para excluir) ---
        elif not df_editado.drop(columns=["🗑️"]).equals(st.session_state.df_saldos):
            # Atualiza apenas os dados reais
            st.session_state.df_saldos = df_editado.drop(columns=["🗑️"])
            Database.salvar_saldos(st.session_state.df_saldos)
            st.toast("Saldos atualizados!", icon="💰")
            st.rerun()

        total = st.session_state.df_saldos['valor'].sum()
        st.info(f"**Total Disponível:** R$ {total:,.2f}")
    else:
        st.info("Nenhuma conta registrada ainda.")