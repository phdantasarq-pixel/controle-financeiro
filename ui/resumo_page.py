import streamlit as st
import pandas as pd
from domain.resumo import resumo_mensal
from ui.components import seletor_meses_inteligente
from services.database import Database
from datetime import datetime
import re


def resumo_page(df):
    st.header("📊 Resumo Financeiro")

    if df.empty:
        st.warning("Nenhum dado encontrado no MongoDB.")
        return

    # --- FILTRO INTELIGENTE ---
    st.write("### 📅 Filtrar por Período")
    mes_sel = seletor_meses_inteligente(key_suffix="resumo_financeiro")

    # Cálculos de topo
    receitas, despesas, saldo = resumo_mensal(df, mes_sel)
    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", f"R$ {receitas:,.2f}")
    c2.metric("Despesas", f"R$ {despesas:,.2f}")
    c3.metric("Saldo", f"R$ {saldo:,.2f}")

    # Tipagem e Cópia para filtragem
    df_p = df.copy()
    df_p['data_vencimento'] = pd.to_datetime(df_p['data_vencimento'], errors='coerce')

    m, a = map(int, mes_sel.split('/'))
    df_f = df_p[(df_p['data_vencimento'].dt.month == m) & (df_p['data_vencimento'].dt.year == a)]

    if not df_f.empty:
        st.subheader("📝 Lançamentos do Período")
        st.caption("✨ **Autosave ativado:** Alterações são salvas automaticamente ao editar as células.")

        # --- LÓGICA DE AUTOSAVE ---
        def processar_edicao():
            # Pega as mudanças pendentes no editor
            state = st.session_state.editor_financeiro
            if state["edited_rows"]:
                with st.spinner("Salvando alterações..."):
                    for row_idx_str, changes in state["edited_rows"].items():
                        # O Streamlit retorna o índice da linha filtrada (df_f)
                        row_idx = int(row_idx_str)
                        # Localizamos o índice real no dataframe principal através da posição na fatia df_f
                        real_idx = df_f.index[row_idx]

                        # Aplica as mudanças no dataframe global
                        for field, value in changes.items():
                            st.session_state.df.at[real_idx, field] = value

                    # Salva no MongoDB
                    Database.salvar_dados(st.session_state.df)
                    st.toast("Alterações salvas com sucesso!", icon="✅")

        # --- EDITOR DE DADOS COM AUTOSAVE ---
        st.data_editor(
            df_f,
            use_container_width=True,
            hide_index=True,
            column_config={
                "data_vencimento": st.column_config.DateColumn("Vencimento", format="DD-MM-YYYY"),
                "data_registro": None,
                "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f", min_value=0),
                "tipo": st.column_config.SelectboxColumn("Tipo", options=["Receita", "Despesa"]),
                "natureza": st.column_config.SelectboxColumn("Natureza", options=["Fixo", "Variável"]),
                "categoria": "Categoria",
                "descricao": "Descrição"
            },
            key="editor_financeiro",
            on_change=processar_edicao  # Gatilho para o Autosave
        )

        st.write("---")
        st.subheader("🗑️ Gerenciar Lançamento")

        # Preparação para exclusão (usamos df_f pois o editor altera o session_state direto)
        df_view = df_f.copy()
        df_view['selecao_label'] = df_view['descricao'] + " (R$ " + df_view['valor'].map('{:,.2f}'.format) + ")"
        dict_referencia = {row['selecao_label']: idx for idx, row in df_view.iterrows()}

        item_selecionado = st.selectbox("Selecione para remover permanentemente:",
                                        options=[""] + list(dict_referencia.keys()))

        if item_selecionado != "":
            idx_alvo = dict_referencia[item_selecionado]
            descricao_original = st.session_state.df.loc[idx_alvo, 'descricao']
            is_parcela = bool(re.search(r'\(\d+/\d+\)', descricao_original))

            col_ex1, col_ex2 = st.columns(2)
            with col_ex1:
                if st.button("❌ Excluir Registro", use_container_width=True):
                    st.session_state.df = st.session_state.df.drop(idx_alvo)
                    Database.salvar_dados(st.session_state.df)
                    st.success("Item removido!")
                    st.rerun()

            with col_ex2:
                if is_parcela:
                    if st.button("🧨 Excluir TODAS as parcelas", use_container_width=True, type="primary"):
                        nome_base = descricao_original.split(" (")[0].strip()
                        mascara = st.session_state.df['descricao'].str.contains(re.escape(nome_base), na=False)
                        st.session_state.df = st.session_state.df[~mascara]
                        Database.salvar_dados(st.session_state.df)
                        st.success("Parcelas removidas!")
                        st.rerun()
    else:
        st.info(f"Nenhum lançamento encontrado para {mes_sel}.")