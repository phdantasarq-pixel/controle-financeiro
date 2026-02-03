import streamlit as st
import pandas as pd
from ui.components import seletor_meses_inteligente
from services.database import Database
from datetime import datetime


def resumo_page(df: pd.DataFrame):
    st.header("📊 Resumo Financeiro")

    if df.empty:
        st.warning("Nenhum dado encontrado. Cadastre no menu Novo lançamento.")
        return

    # =====================================================
    # ESTADOS GLOBAIS
    # =====================================================
    if "lixeira_estado" not in st.session_state:
        st.session_state.lixeira_estado = {}

    # =====================================================
    # FILTRO INTELIGENTE
    # =====================================================
    mes_sel = seletor_meses_inteligente(key_suffix="resumo_financeiro")
    m_sel, a_sel = map(int, mes_sel.split("/"))
    hoje = datetime.now()

    # =====================================================
    # SALDO REAL ATUAL EM CONTAS [H8.1]
    # =====================================================
    saldo_atual_contas = Database.obter_total_saldos_real()

    # =====================================================
    # PREPARAÇÃO DOS DADOS
    # =====================================================
    df_p = df.copy()
    df_p["data_vencimento"] = pd.to_datetime(df_p["data_vencimento"], errors="coerce")

    if "status" not in df_p.columns:
        df_p["status"] = "🟡 Pendente"

    def limpa_status(s):
        s = str(s)
        if "Concluído" in s: return "Concluído"
        if "Atrasado" in s: return "Atrasado"
        return "Pendente"

    # =====================================================
    # LÓGICA DE SALDO PROJETADO [H8.1]
    # =====================================================
    df_mes_atual = df_p[
        (df_p["data_vencimento"].dt.month == hoje.month) &
        (df_p["data_vencimento"].dt.year == hoje.year)
        ].copy()

    rec_pend_atual = df_mes_atual[
        (df_mes_atual["tipo"] == "Receita") & (~df_mes_atual["status"].str.contains("Concluído", na=False))
        ]["valor"].sum()

    desp_pend_atual = df_mes_atual[
        (df_mes_atual["tipo"] == "Despesa") & (~df_mes_atual["status"].str.contains("Concluído", na=False))
        ]["valor"].sum()

    saldo_fechamento_atual = saldo_atual_contas + rec_pend_atual - desp_pend_atual

    # =====================================================
    # FILTRO DO MÊS SELECIONADO PARA EXIBIÇÃO
    # =====================================================
    mask = (df_p["data_vencimento"].dt.month == m_sel) & (df_p["data_vencimento"].dt.year == a_sel)
    df_f = df_p[mask].copy()

    total_receitas_mes = df_f[df_f["tipo"] == "Receita"]["valor"].sum()
    total_despesas_mes = df_f[df_f["tipo"] == "Despesa"]["valor"].sum()
    balanco_mensal = total_receitas_mes - total_despesas_mes

    if m_sel == hoje.month and a_sel == hoje.year:
        saldo_exibicao = saldo_fechamento_atual
        label_status = "Saldo Livre (Fim do Mês)"
        ajuda_texto = "Saldo atual em conta + receitas pendentes - despesas pendentes do mês."
    else:
        saldo_exibicao = saldo_fechamento_atual + balanco_mensal
        label_status = f"Saldo Projetado ({mes_sel})"
        ajuda_texto = f"Previsão de saldo considerando o fechamento de hoje e o balanço de {mes_sel}."

    hoje_pd = pd.Timestamp(hoje.date())

    def aplicar_emoji(row):
        st_limpo = limpa_status(row["status"])
        if st_limpo == "Concluído": return "🟢 Concluído"
        if pd.notnull(row["data_vencimento"]) and row["data_vencimento"] < hoje_pd: return "🔴 Atrasado"
        return "🟡 Pendente"

    df_f["Situacao"] = df_f.apply(aplicar_emoji, axis=1)

    # =====================================================
    # RENDERIZAÇÃO DE KPIs E ACORDION
    # =====================================================
    with st.expander("🏦 Saldo em Tempo Real & Reserva", expanded=True):
        c_l1, c_l2, c_l3 = st.columns(3)
        c_l1.metric("💰 Saldo em Contas (Hoje)", f"R$ {saldo_atual_contas:,.2f}")
        c_l2.metric("📊 Balanço do Mês", f"R$ {balanco_mensal:,.2f}")
        c_l3.metric(label_status, f"R$ {saldo_exibicao:,.2f}",
                    delta_color="normal" if saldo_exibicao >= 0 else "inverse")
        st.caption(f"💡 {ajuda_texto}")

    st.divider()

    # =====================================================
    # TABELAS COM EDITOR (SALVAMENTO REATIVO + EXCLUSÃO)
    # =====================================================
    config_colunas = {
        "🗑️": st.column_config.CheckboxColumn("Excluir", default=False),
        "Situacao": st.column_config.SelectboxColumn(
            "Status", options=["🟢 Concluído", "🟡 Pendente", "🔴 Atrasado"], width=130
        ),
        "data_vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
        "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
    }

    for tipo, label, icon in [("Receita", "Receitas", "💰"), ("Despesa", "Despesas", "💸")]:
        df_tipo = df_f[df_f["tipo"] == tipo].copy()

        # ... (dentro do loop for tipo, label, icon)

        with st.expander(f"{icon} {label} — Total: R$ {df_tipo['valor'].sum():,.2f}", expanded=True):
            if df_tipo.empty:
                st.info(f"Nenhuma {tipo.lower()} registrada.")
                continue

            df_tipo["original_index"] = df_tipo.index
            df_tipo["🗑️"] = False

            # Definimos as colunas de visualização com a lixeira no final
            cols_view = ["Situacao", "data_vencimento", "descricao", "categoria", "valor", "🗑️"]

            # 1. Renderiza o editor primeiro
            df_editado = st.data_editor(
                df_tipo[cols_view + ["original_index"]],
                hide_index=True,
                use_container_width=True,
                column_config={**config_colunas, "original_index": None},
                key=f"editor_{tipo.lower()}_{m_sel}_{a_sel}"
            )

            # 2. Inicializa itens_excluir como lista vazia (Evita o UnboundLocalError)
            itens_excluir = []

            # 3. Verifica se houve edição/exclusão
            if df_editado is not None:
                itens_excluir = df_editado[df_editado["🗑️"] == True]["original_index"].tolist()

            # --- LOGICA DE EXCLUSÃO ---
            if itens_excluir:
                if st.button(f"🗑️ Confirmar Exclusão ({len(itens_excluir)})", key=f"btn_del_{tipo}_{m_sel}"):
                    st.session_state.df = st.session_state.df.drop(itens_excluir)
                    Database.salvar_dados(st.session_state.df)
                    st.rerun()

            # --- LOGICA DE AUTOSAVE ---
            else:
                # Comparamos ignorando a coluna de lixeira e o original_index
                colunas_dados = ["Situacao", "data_vencimento", "descricao", "categoria", "valor"]
                if not df_editado[colunas_dados].equals(df_tipo[colunas_dados]):
                    for _, row in df_editado.iterrows():
                        idx_orig = row["original_index"]
                        st.session_state.df.at[idx_orig, "status"] = row["Situacao"]
                        st.session_state.df.at[idx_orig, "valor"] = row["valor"]
                        st.session_state.df.at[idx_orig, "data_vencimento"] = row["data_vencimento"]
                        st.session_state.df.at[idx_orig, "descricao"] = row["descricao"]
                        st.session_state.df.at[idx_orig, "categoria"] = row["categoria"]

                    Database.salvar_dados(st.session_state.df)
                    st.rerun()