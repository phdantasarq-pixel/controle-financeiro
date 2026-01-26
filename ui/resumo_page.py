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
        df_p['data_vencimento'] = pd.to_datetime(df_p['data_vencimento'], format='mixed')
        m, a = map(int, mes_sel.split('/'))
        df_f = df_p[(df_p['data_vencimento'].dt.month == m) & (df_p['data_vencimento'].dt.year == a)].copy()

        # Exibição da Tabela
        st.dataframe(
            df_f.sort_values("data_vencimento"),
            use_container_width=True,
            hide_index=False,  # Precisamos do index para a exclusão
            column_config={
                "data_vencimento": st.column_config.DateColumn("Vencimento", format="DD-MM-YYYY"),
                "data_registro": st.column_config.DateColumn("Registro", format="DD-MM-YYYY"),
                "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
            }
        )

        st.write("---")
        st.subheader("🗑️ Excluir Lançamento")

        # Criamos uma lista amigável para o seletor de exclusão
        df_f['selecao'] = df_f.index.astype(str) + " - " + df_f['descricao'] + " (R$ " + df_f['valor'].astype(str) + ")"
        item_para_excluir = st.selectbox("Selecione o item que deseja remover:",
                                         options=[""] + df_f['selecao'].tolist())

        if item_para_excluir != "":
            idx_escolhido = int(item_para_excluir.split(" - ")[0])
            linha_alvo = df.loc[idx_escolhido]
            descricao_original = linha_alvo['descricao']

            # Lógica para detectar se é parcelamento (ex: "Compra (1/5)")
            is_parcela = "(" in descricao_original and "/" in descricao_original

            col_ex1, col_ex2 = st.columns(2)

            with col_ex1:
                if st.button("❌ Excluir APENAS este", use_container_width=True):
                    st.session_state.df = df.drop(idx_escolhido)
                    Database.salvar_dados(st.session_state.df)
                    st.success("Item excluído!")
                    st.rerun()

            with col_ex2:
                if is_parcela:
                    if st.button("🧨 Excluir TODAS as parcelas", use_container_width=True):
                        # Extrai o nome base antes do (1/10)
                        nome_base = descricao_original.split(" (")[0]
                        # Filtra tudo que contém o mesmo nome base
                        # Usamos str.contains para pegar todas as parcelas futuras e passadas
                        mascara_exclusao = df['descricao'].str.contains(re.escape(nome_base), na=False)
                        qtd_removida = mascara_exclusao.sum()

                        st.session_state.df = df[~mascara_exclusao]
                        Database.salvar_dados(st.session_state.df)
                        st.success(f"{qtd_removida} parcelas removidas com sucesso!")
                        st.rerun()
                else:
                    st.info("Este item não parece ser um parcelamento.")

    else:
        st.info("Nenhum dado encontrado para este mês.")