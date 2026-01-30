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

    # --- CÁLCULOS E FILTRAGEM ---
    m, a = map(int, mes_sel.split('/'))
    df_p = df.copy()
    df_p['data_vencimento'] = pd.to_datetime(df_p['data_vencimento'], errors='coerce')
    df_f = df_p[(df_p['data_vencimento'].dt.month == m) & (df_p['data_vencimento'].dt.year == a)].copy()

    if 'status' not in df_f.columns:
        df_f['status'] = 'Pendente'

    # --- LÓGICA DE SINALIZAÇÃO ---
    def sinalizar_status(row):
        hoje = pd.Timestamp(datetime.now().date())
        vencimento = row['data_vencimento']
        if row['status'] == "Concluído":
            return "🟢 Pago"
        elif pd.notnull(vencimento) and vencimento < hoje:
            return "🔴 Atrasado"
        else:
            return "🟡 No Prazo"

    df_f['Sinalizador'] = df_f.apply(sinalizar_status, axis=1)

    # --- CÁLCULOS DE MÉTRICAS ---
    receitas_pagas = df_f[(df_f['tipo'] == "Receita") & (df_f['status'] == "Concluído")]['valor'].sum()
    despesas_pagas = df_f[(df_f['tipo'] == "Despesa") & (df_f['status'] == "Concluído")]['valor'].sum()
    saldo_real_mes = receitas_pagas - despesas_pagas
    a_receber_mes = df_f[(df_f['tipo'] == "Receita") & (df_f['status'] != "Concluído")]['valor'].sum()
    a_pagar_mes = df_f[(df_f['tipo'] == "Despesa") & (df_f['status'] != "Concluído")]['valor'].sum()
    saldo_pendente = a_receber_mes - a_pagar_mes

    # --- LAYOUT COM ACCORDIONS ---
    with st.expander("💰 Ver Realizado no Mês", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.metric("✅ Recebido", f"R$ {receitas_pagas:,.2f}")
        c2.metric("💸 Pago", f"R$ {despesas_pagas:,.2f}")
        c3.metric("📊 Saldo Atual", f"R$ {saldo_real_mes:,.2f}")

    with st.expander("⏳ Pendente / Projeção", expanded=True):
        c4, c5, c6 = st.columns(3)
        c4.metric("💰 A Receber", f"R$ {a_receber_mes:,.2f}")
        c5.metric("⚠️ A Pagar", f"R$ {a_pagar_mes:,.2f}", delta_color="inverse")
        c6.metric("⚖️ Saldo Pendente", f"R$ {saldo_pendente:,.2f}",
                  delta_color="normal" if saldo_pendente >= 0 else "inverse")

    st.write("---")

    if not df_f.empty:
        st.subheader("📝 Lançamentos do Período")

        # --- CORREÇÃO DO AUTOSAVE (Sem st.rerun no callback) ---
        def processar_edicao():
            state = st.session_state.editor_financeiro
            if state["edited_rows"]:
                # Sincroniza as mudanças do editor com o DataFrame principal na session_state
                for row_idx_str, changes in state["edited_rows"].items():
                    row_idx = int(row_idx_str)
                    real_idx = df_f.index[row_idx]
                    for field, value in changes.items():
                        st.session_state.df.at[real_idx, field] = value

                # Salva no MongoDB
                Database.salvar_dados(st.session_state.df)
                # O Streamlit atualizará a página automaticamente após o callback terminar

        st.data_editor(
            df_f,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Sinalizador": st.column_config.TextColumn("Alerta"),
                "status": st.column_config.SelectboxColumn("📊 Status", options=["Pendente", "Concluído"]),
                "data_vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
                "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "tipo": st.column_config.SelectboxColumn("Tipo", options=["Receita", "Despesa"]),
                "descricao": "Descrição",
                "natureza": None, "categoria": None, "data_registro": None, "created_at": None, "id": None, "_id": None
            },
            key="editor_financeiro",
            on_change=processar_edicao,
            disabled=["Sinalizador"]
        )

        # --- GERENCIAR LANÇAMENTO (EXCLUSÃO) ---
        st.write("---")
        st.subheader("🗑️ Gerenciar Lançamento")
        df_view = df_f.copy()
        df_view['selecao_label'] = df_view['descricao'] + " (R$ " + df_view['valor'].map('{:,.2f}'.format) + ")"
        dict_referencia = {row['selecao_label']: idx for idx, row in df_view.iterrows()}

        item_selecionado = st.selectbox("Selecione para remover:", options=[""] + list(dict_referencia.keys()))

        if item_selecionado != "":
            idx_alvo = dict_referencia[item_selecionado]
            descricao_original = st.session_state.df.loc[idx_alvo, 'descricao']
            is_parcela = bool(re.search(r'\(\d+/\d+\)', descricao_original))

            c_ex1, c_ex2 = st.columns(2)
            with c_ex1:
                # Aqui o st.rerun() PODE ser usado porque estamos dentro de um st.button (não é callback)
                if st.button("❌ Excluir Registro", use_container_width=True):
                    st.session_state.df = st.session_state.df.drop(idx_alvo)
                    Database.salvar_dados(st.session_state.df)
                    st.rerun()

            with c_ex2:
                if is_parcela:
                    if st.button("🧨 Excluir TODAS as parcelas", use_container_width=True, type="primary"):
                        nome_base = descricao_original.split(" (")[0].strip()
                        mascara = st.session_state.df['descricao'].str.contains(re.escape(nome_base), na=False)
                        st.session_state.df = st.session_state.df[~mascara]
                        Database.salvar_dados(st.session_state.df)
                        st.rerun()
    else:
        st.info(f"Nenhum lançamento encontrado para {mes_sel}.")