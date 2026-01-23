import streamlit as st
import pandas as pd
from domain.resumo import resumo_mensal
from services.calendar_service import mes_ano
from services.database import Database


def resumo_page(df):
    st.header("📊 Resumo Financeiro")

    opcoes = mes_ano()
    mes_selecionado = st.selectbox("Selecione o período:", opcoes)

    # Nota: Certifique-se que resumo_mensal usa 'data_vencimento' agora
    receitas, despesas, saldo = resumo_mensal(df, mes_selecionado)

    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", f"R$ {receitas:,.2f}")
    c2.metric("Despesas", f"R$ {despesas:,.2f}")
    c3.metric("Saldo Atual", f"R$ {saldo:,.2f}", delta=float(saldo))

    if not df.empty:
        st.subheader("Extrato Detalhado")

        # 1. Definimos a ordem das colunas e removemos a 'data' antiga da exibição
        colunas_exibicao = [
            "data_registro",
            "data_vencimento",
            "tipo",
            "natureza",
            "valor",
            "categoria",
            "descricao"
        ]

        df_editado = st.data_editor(
            df,
            column_order=colunas_exibicao,  # Remove 'data' e organiza o resto
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                # 2. Formata data_registro para padrão BR (apenas data, sem hora)
                "data_registro": st.column_config.DateColumn(
                    "Data Lançamento",
                    format="DD/MM/YYYY",
                    disabled=True
                ),
                "data_vencimento": st.column_config.DateColumn(
                    "Vencimento",
                    format="DD/MM/YYYY"
                ),
                "tipo": st.column_config.SelectboxColumn("Tipo", options=["Receita", "Despesa"]),
                "natureza": st.column_config.SelectboxColumn("Natureza", options=["Fixo", "Variável"]),
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
            }
        )

        if not df_editado.equals(df):
            if st.button("💾 Salvar Alterações"):
                st.session_state.df = df_editado
                Database.salvar_dados(df_editado)
                st.rerun()