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
        # Criamos uma cópia para não afetar o estado original durante a filtragem
        df_p = df.copy()

        # Tipagem para evitar erro de renderização do PyArrow
        df_p['data_vencimento'] = pd.to_datetime(df_p['data_vencimento'], errors='coerce')
        df_p['data_registro'] = pd.to_datetime(df_p['data_registro'], errors='coerce')

        m, a = map(int, mes_sel.split('/'))
        # Filtramos mantendo os índices originais para permitir a edição no df principal
        df_f = df_p[(df_p['data_vencimento'].dt.month == m) & (df_p['data_vencimento'].dt.year == a)]

        st.subheader("📝 Lançamentos do Período")
        st.caption("Dica: Clique duas vezes em um campo para editar. A data de registro está oculta para um visual mais limpo.")

        # --- EDITOR DE DADOS ---
        # A coluna 'data_registro' é ocultada definindo como None no column_config
        df_editado = st.data_editor(
            df_f,
            use_container_width=True,
            hide_index=True,
            column_config={
                "data_vencimento": st.column_config.DateColumn("Vencimento", format="DD-MM-YYYY"),
                "data_registro": None,  # Oculta a coluna da visualização
                "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f", min_value=0),
                "tipo": st.column_config.SelectboxColumn("Tipo", options=["Receita", "Despesa"]),
                "natureza": st.column_config.SelectboxColumn("Natureza", options=["Fixo", "Variável"]),
                "categoria": "Categoria",
                "descricao": "Descrição"
            },
            key="editor_financeiro"
        )

        # Verifica se houve alterações na tabela
        if not df_editado.equals(df_f):
            col_save1, col_save2 = st.columns([1, 3])
            with col_save1:
                if st.button("💾 Salvar Alterações", use_container_width=True, type="primary"):
                    with st.spinner("Sincronizando com MongoDB..."):
                        # Atualiza o DataFrame global no session_state
                        st.session_state.df.update(df_editado)
                        # Persiste as mudanças no banco de dados
                        Database.salvar_dados(st.session_state.df)
                    st.success("Dados atualizados!")
                    st.rerun()
            with col_save2:
                st.info("Detectamos alterações na tabela. Não esqueça de salvar!")

        st.write("---")
        st.subheader("🗑️ Gerenciar Lançamento")

        # Criamos uma label amigável para exclusão refletindo o estado atual do editor
        df_f_view = df_editado.copy()
        df_f_view['selecao_label'] = df_f_view['descricao'] + " (R$ " + df_f_view['valor'].map('{:,.2f}'.format) + ")"

        # Mapeia a label para o índice original do DataFrame principal
        dict_referencia = {row['selecao_label']: idx for idx, row in df_f_view.iterrows()}

        item_selecionado = st.selectbox("Selecione o item para remover permanentemente:",
                                        options=[""] + list(dict_referencia.keys()))

        if item_selecionado != "":
            idx_alvo = dict_referencia[item_selecionado]
            descricao_original = st.session_state.df.loc[idx_alvo, 'descricao']
            is_parcela = bool(re.search(r'\(\d+/\d+\)', descricao_original))

            col_ex1, col_ex2 = st.columns(2)

            with col_ex1:
                if st.button("❌ Excluir APENAS este", use_container_width=True):
                    with st.spinner("Removendo registro do banco..."):
                        st.session_state.df = st.session_state.df.drop(idx_alvo)
                        Database.salvar_dados(st.session_state.df)
                    st.success("Item removido!")
                    st.rerun()

            with col_ex2:
                if is_parcela:
                    if st.button("🧨 Excluir TODAS as parcelas", use_container_width=True, type="primary"):
                        with st.spinner("Limpando grupo de parcelas..."):
                            nome_base = descricao_original.split(" (")[0].strip()
                            mascara = st.session_state.df['descricao'].str.contains(re.escape(nome_base), na=False)
                            st.session_state.df = st.session_state.df[~mascara]
                            Database.salvar_dados(st.session_state.df)
                        st.success("Parcelas removidas!")
                        st.rerun()
                else:
                    st.info("💡 Este item não faz parte de um parcelamento.")

    else:
        st.info("Nenhum dado encontrado para este mês.")