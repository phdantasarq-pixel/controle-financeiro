import streamlit as st
import pandas as pd
from domain.resumo import resumo_mensal
from services.calendar_service import mes_ano
from services.database import Database

def resumo_page(df):
    st.header("📊 Resumo Financeiro")

    # Filtro de Meses
    opcoes = mes_ano()
    mes_selecionado = st.selectbox("Selecione o período:", opcoes)

    # Cálculo do resumo baseado no mês selecionado
    receitas, despesas, saldo = resumo_mensal(df, mes_selecionado)

    # Exibição das métricas
    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", f"R$ {receitas:,.2f}")
    c2.metric("Despesas", f"R$ {despesas:,.2f}")
    c3.metric("Saldo Atual", f"R$ {saldo:,.2f}", delta=float(saldo))

    if not df.empty:
        st.subheader("Extrato Detalhado")
        st.info("💡 A tabela abaixo está ordenada automaticamente pela data de vencimento.")

        # 1. ORDENAÇÃO: Ordena o DataFrame pela data de vencimento (mais antiga primeiro)
        # Usamos inplace=False para não gerar avisos de cópia do Pandas
        df_exibicao = df.sort_values(by="data_vencimento", ascending=True)

        # 2. COLUNAS VISÍVEIS: Definimos o que aparece (ocultando data_registro e data)
        colunas_visiveis = [
            "data_vencimento",
            "tipo",
            "natureza",
            "valor",
            "categoria",
            "descricao"
        ]

        # 3. CONFIGURAÇÃO DO EDITOR
        df_editado = st.data_editor(
            df_exibicao,
            column_order=colunas_visiveis,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "data_vencimento": st.column_config.DateColumn(
                    "Vencimento",
                    format="DD/MM/YYYY"
                ),
                "tipo": st.column_config.SelectboxColumn(
                    "Tipo",
                    options=["Receita", "Despesa"]
                ),
                "natureza": st.column_config.SelectboxColumn(
                    "Natureza",
                    options=["Fixo", "Variável"]
                ),
                "valor": st.column_config.NumberColumn(
                    "Valor (R$)",
                    format="R$ %.2f"
                ),
                "categoria": st.column_config.TextColumn("Categoria"),
                "descricao": st.column_config.TextColumn("Descrição")
            }
        )

        # 4. LÓGICA PARA SALVAR ALTERAÇÕES
        # Comparamos o editado com o de exibição para detectar mudanças
        if not df_editado.equals(df_exibicao):
            if st.button("💾 Salvar Alterações"):
                # Atualizamos o estado global e o arquivo físico
                st.session_state.df = df_editado
                if Database.salvar_dados(df_editado):
                    st.success("Alterações salvas com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao salvar no banco de dados.")