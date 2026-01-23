import streamlit as st
import pandas as pd
from domain.resumo import resumo_mensal
from services.calendar_service import mes_ano
from services.database import Database  # Importação atualizada

def resumo_page(df):
    st.header("📊 Resumo Financeiro")

    # Filtro de Meses
    opcoes = mes_ano()
    mes_selecionado = st.selectbox("Selecione o período:", opcoes)

    receitas, despesas, saldo = resumo_mensal(df, mes_selecionado)

    # Exibição em Cartões
    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", f"R$ {receitas:,.2f}")
    c2.metric("Despesas", f"R$ {despesas:,.2f}")
    c3.metric("Saldo Atual", f"R$ {saldo:,.2f}", delta=float(saldo))

    if not df.empty:
        st.subheader("Extrato Detalhado")
        st.info("💡 Clique nas células para editar ou selecione a linha e aperte 'Delete' para excluir.")

        # O componente data_editor captura edições e exclusões automaticamente
        df_editado = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic", # Permite excluir linhas
            column_config={
                "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "tipo": st.column_config.SelectboxColumn("Tipo", options=["Receita", "Despesa"]),
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                "categoria": st.column_config.TextColumn("Categoria"),
                "descricao": st.column_config.TextColumn("Descrição")
            }
        )

        # Se o DataFrame editado for diferente do original, habilitamos o salvamento
        if not df_editado.equals(df):
            if st.button("💾 Salvar Alterações Permanentemente"):
                # Atualiza o estado da sessão e o arquivo físico
                st.session_state.df = df_editado
                if Database.salvar_dados(df_editado):
                    st.success("Dados atualizados com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao salvar no arquivo dados.json.")