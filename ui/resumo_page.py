import streamlit as st
import pandas as pd
from domain.resumo import resumo_mensal
from services.calendar_service import mes_ano
from services.database import Database
from datetime import datetime
import re


def resumo_page(df):
    st.header("📊 Resumo Financeiro")

    opcoes = mes_ano()
    mes_sel = st.segmented_control("Meses", options=opcoes,
                                   default=datetime.now().strftime("%m/%Y")) or datetime.now().strftime("%m/%Y")

    receitas, despesas, saldo = resumo_mensal(df, mes_sel)
    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", f"R$ {receitas:,.2f}")
    c2.metric("Despesas", f"R$ {despesas:,.2f}")
    c3.metric("Saldo", f"R$ {saldo:,.2f}")

    if not df.empty:
        df_p = df.copy()
        # Blindagem contra erro de tipos (H2.5 / PyArrow)
        df_p['data_vencimento'] = pd.to_datetime(df_p['data_vencimento'], errors='coerce')
        df_p['data_registro'] = pd.to_datetime(df_p['data_registro'], errors='coerce')

        m, a = map(int, mes_sel.split('/'))
        df_f = df_p[(df_p['data_vencimento'].dt.month == m) & (df_p['data_vencimento'].dt.year == a)].copy()

        st.dataframe(
            df_f.sort_values("data_vencimento"),
            use_container_width=True,
            hide_index=False,
            column_config={
                "data_vencimento": st.column_config.DateColumn("Vencimento", format="DD-MM-YYYY"),
                "data_registro": st.column_config.DateColumn("Registro", format="DD-MM-YYYY"),
                "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "tipo": "Tipo", "natureza": "Natureza", "categoria": "Categoria", "descricao": "Descrição"
            }
        )

        st.write("---")
        st.subheader("🗑️ Gerenciar Lançamento")

        # Lista formatada para o selectbox
        df_f['selecao'] = df_f['id'] + " - " + df_f['descricao'] + " (R$ " + df_f['valor'].map(
            '{:,.2f}'.format) + ")"
        item_para_excluir = st.selectbox(
            "Selecione o item para remover:", options=[""] + df_f['selecao'].tolist()
        )

        if item_para_excluir != "":
            id_escolhido = item_para_excluir.split(" - ")[0]
            linha_alvo = df[df['id'] == id_escolhido].iloc[0]

            descricao_original = linha_alvo['descricao']
            is_parcela = bool(re.search(r'\(\d+/\d+\)', descricao_original))

            col_ex1, col_ex2 = st.columns(2)

            with col_ex1:
                if st.button("❌ Excluir APENAS este", use_container_width=True):
                    with st.spinner("Excluindo registro..."):
                        st.session_state.df = df.drop(idx_escolhido)
                        Database.salvar_dados(st.session_state.df)
                    st.rerun()

            with col_ex2:
                if is_parcela:
                    if st.button("🧨 Excluir TODAS as parcelas", use_container_width=True, type="primary"):
                        with st.spinner("Removendo todas as parcelas do grupo..."):
                            nome_base = descricao_original.split(" (")[0].strip()
                            mascara_exclusao = df['descricao'].str.contains(re.escape(nome_base), na=False)
                            st.session_state.df = df[~mascara_exclusao]
                            Database.salvar_dados(st.session_state.df)
                        st.rerun()
                else:
                    st.info("💡 Este item não possui parcelas vinculadas.")
    else:
        st.info("Nenhum dado encontrado para este mês.")