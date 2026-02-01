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
    mes_sel = seletor_meses_inteligente(key_suffix="resumo_financeiro")

    # --- 1. BUSCAR SALDO REAL ATUAL ---
    contas = Database.listar_contas() if hasattr(Database, 'listar_contas') else []
    saldo_atual_contas = sum(conta.get('saldo', 0) for conta in contas)

    # --- 2. FILTRAGEM DO MÊS ---
    m, a = map(int, mes_sel.split('/'))
    df_p = df.copy()
    df_p['data_vencimento'] = pd.to_datetime(df_p['data_vencimento'], errors='coerce')
    df_f = df_p[(df_p['data_vencimento'].dt.month == m) & (df_p['data_vencimento'].dt.year == a)].copy()

    if 'status' not in df_f.columns:
        df_f['status'] = 'Pendente'

    # --- 3. LÓGICA UNIFICADA: BOLINHA COMO STATUS EDITÁVEL ---
    def obter_situacao(row):
        hoje = pd.Timestamp(datetime.now().date())
        vencimento = row['data_vencimento']
        if row['status'] == "Concluído":
            return "🟢 Concluído"
        elif pd.notnull(vencimento) and vencimento < hoje:
            return "🔴 Atrasado"
        else:
            return "🟡 Pendente"

    df_f['Situacao'] = df_f.apply(obter_situacao, axis=1)

    # ✂️ Limitar visualmente a 20 caracteres
    df_f['descricao_curta'] = df_f['descricao'].apply(lambda x: (str(x)[:17] + '...') if len(str(x)) > 20 else str(x))

    # --- 4. CÁLCULOS E CONTADORES ---
    total_receitas_mes = df_f[df_f['tipo'] == "Receita"]['valor'].sum()
    total_despesas_mes = df_f[df_f['tipo'] == "Despesa"]['valor'].sum()
    resultado_mes = total_receitas_mes - total_despesas_mes

    itens_concluidos = len(df_f[df_f['status'] == "Concluído"])
    itens_pendentes = len(df_f[df_f['status'] != "Concluído"])
    valor_pendente_pagar = df_f[(df_f['tipo'] == "Despesa") & (df_f['status'] != "Concluído")]['valor'].sum()

    saldo_projetado_final = saldo_atual_contas + total_receitas_mes - total_despesas_mes

    # --- EXIBIÇÃO DO TOPO ---
    c_count1, c_count2, c_count3 = st.columns(3)
    c_count1.success(f"✅ **Concluídos:** {itens_concluidos}")
    c_count2.warning(f"⏳ **Pendentes:** {itens_pendentes}")
    c_count3.error(f"💸 **A Pagar:** R$ {valor_pendente_pagar:,.2f}")

    with st.expander("🏁 Projeção Final (Cálculo Fixo)", expanded=True):
        c4, c5, c6 = st.columns(3)
        c4.metric("💰 Receitas (Total)", f"R$ {total_receitas_mes:,.2f}")
        c5.metric("⚠️ Despesas (Total)", f"R$ {total_despesas_mes:,.2f}", delta_color="inverse")
        c6.metric(
            "🚀 Saldo Projetado Final",
            f"R$ {saldo_projetado_final:,.2f}",
            delta=f"Mês: R$ {resultado_mes:,.2f}",
            delta_color="normal" if resultado_mes >= 0 else "inverse"
        )

    st.write("---")

    if not df_f.empty:
        # --- FUNÇÃO DE SALVAMENTO UNIFICADA ---
        def processar_edicao_v2(key_editor, dataframe_origem):
            state = st.session_state[key_editor]
            if state["edited_rows"]:
                for row_idx_str, changes in state["edited_rows"].items():
                    row_idx = int(row_idx_str)
                    real_idx = dataframe_origem.index[row_idx]
                    for field, value in changes.items():
                        # Se alterar a Situacao (bolinha), mapeia de volta para o banco
                        if field == 'Situacao':
                            novo_status = "Concluído" if "🟢" in value else "Pendente"
                            st.session_state.df.at[real_idx, 'status'] = novo_status
                        elif field == 'descricao_curta':
                            st.session_state.df.at[real_idx, 'descricao'] = value
                        else:
                            st.session_state.df.at[real_idx, field] = value
                Database.salvar_dados(st.session_state.df)
                st.rerun()

        # CONFIGURAÇÃO DE COLUNAS (Removida a coluna status antiga)
        config_colunas = {
            "Situacao": st.column_config.SelectboxColumn(
                "Status",
                options=["🟢 Concluído", "🟡 Pendente", "🔴 Atrasado"],
                width="small"
            ),
            "data_vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
            "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
            "descricao_curta": st.column_config.TextColumn("Descrição", width=200)
        }
        colunas_ordem = ['Situacao', 'data_vencimento', 'descricao_curta', 'valor']

        # --- SEÇÃO DE RECEITAS ---
        df_receitas = df_f[df_f['tipo'] == "Receita"][colunas_ordem]
        with st.expander(f"💰 Receitas (R$ {total_receitas_mes:,.2f})", expanded=True):
            if not df_receitas.empty:
                st.data_editor(
                    df_receitas,
                    use_container_width=True,
                    hide_index=True,
                    column_config=config_colunas,
                    key="editor_receitas",
                    on_change=processar_edicao_v2,
                    args=("editor_receitas", df_receitas)
                )

        # --- SEÇÃO DE DESPESAS ---
        df_despesas = df_f[df_f['tipo'] == "Despesa"][colunas_ordem]
        with st.expander(f"💸 Despesas (R$ {total_despesas_mes:,.2f})", expanded=True):
            if not df_despesas.empty:
                st.data_editor(
                    df_despesas,
                    use_container_width=True,
                    hide_index=True,
                    column_config=config_colunas,
                    key="editor_despesas",
                    on_change=processar_edicao_v2,
                    args=("editor_despesas", df_despesas)
                )

        # --- GERENCIAR LANÇAMENTO ---
        st.write("---")
        st.subheader("🗑️ Gerenciar Lançamento")
        df_del = df_f.copy()
        df_del['selecao_label'] = df_del['tipo'] + ": " + df_del['descricao'] + " (R$ " + df_del['valor'].map(
            '{:,.2f}'.format) + ")"
        dict_referencia = {row['selecao_label']: idx for idx, row in df_del.iterrows()}

        item_selecionado = st.selectbox("Selecione para remover:", options=[""] + list(dict_referencia.keys()),
                                        key="select_excluir")

        if item_selecionado != "":
            idx_alvo = dict_referencia[item_selecionado]
            descricao_original = st.session_state.df.loc[idx_alvo, 'descricao']
            is_parcela = bool(re.search(r'\(\d+/\d+\)', descricao_original))

            c_ex1, c_ex2 = st.columns(2)
            with c_ex1:
                if st.button("❌ Excluir Registro", use_container_width=True):
                    st.session_state.df = st.session_state.df.drop(idx_alvo)
                    Database.salvar_dados(st.session_state.df)
                    st.rerun()
            with c_ex2:
                if is_parcela and st.button("🧨 Excluir TODAS as parcelas", use_container_width=True, type="primary"):
                    nome_base = descricao_original.split(" (")[0].strip()
                    mascara = st.session_state.df['descricao'].str.contains(re.escape(nome_base), na=False)
                    st.session_state.df = st.session_state.df[~mascara]
                    Database.salvar_dados(st.session_state.df)
                    st.rerun()
    else:
        st.info(f"Nenhum lançamento encontrado para {mes_sel}.")