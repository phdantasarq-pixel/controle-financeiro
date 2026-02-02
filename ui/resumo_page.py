import streamlit as st
import pandas as pd
from domain.resumo import resumo_mensal
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
    # SALDO REAL ATUAL EM CONTAS
    # =====================================================
    saldo_atual_contas = Database.obter_total_saldos_real()

    # =====================================================
    # PREPARAÇÃO DOS DADOS
    # =====================================================
    df_p = df.copy()
    df_p["data_vencimento"] = pd.to_datetime(df_p["data_vencimento"], errors="coerce")
    df_p = df_p.sort_values(by="data_vencimento")

    # =====================================================
    # SALDO ACUMULADO DO MÊS ATUAL
    # =====================================================
    df_mes_atual = df_p[
        (df_p["data_vencimento"].dt.month == hoje.month)
        & (df_p["data_vencimento"].dt.year == hoje.year)
    ].copy()

    rec_pend_atual = df_mes_atual[
        (df_mes_atual["tipo"] == "Receita") & (df_mes_atual["status"] != "Concluído")
    ]["valor"].sum()

    desp_pend_atual = df_mes_atual[
        (df_mes_atual["tipo"] == "Despesa") & (df_mes_atual["status"] != "Concluído")
    ]["valor"].sum()

    saldo_fechamento_atual = saldo_atual_contas + rec_pend_atual - desp_pend_atual

    # =====================================================
    # FILTRO DO MÊS SELECIONADO
    # =====================================================
    df_f = df_p[
        (df_p["data_vencimento"].dt.month == m_sel)
        & (df_p["data_vencimento"].dt.year == a_sel)
    ].copy()

    if "status" not in df_f.columns:
        df_f["status"] = "Pendente"

    total_receitas_mes = df_f[df_f["tipo"] == "Receita"]["valor"].sum()
    total_despesas_mes = df_f[df_f["tipo"] == "Despesa"]["valor"].sum()
    balanco_mensal = total_receitas_mes - total_despesas_mes

    # =====================================================
    # DEFINIÇÃO DO SALDO A EXIBIR
    # =====================================================
    if m_sel == hoje.month and a_sel == hoje.year:
        saldo_exibicao = saldo_fechamento_atual
        label_status = "Saldo Livre (Fim do Mês)"
        ajuda_texto = "Saldo atual + receitas pendentes − despesas pendentes do mês."
    else:
        saldo_exibicao = saldo_fechamento_atual + balanco_mensal
        label_status = f"Saldo Projetado ({mes_sel})"
        ajuda_texto = f"Resultado acumulado até o fim de {mes_sel}."

    # =====================================================
    # SITUAÇÃO
    # =====================================================
    hoje_pd = pd.Timestamp(hoje.date())

    def obter_situacao(row):
        if row["status"] == "Concluído":
            return "🟢 Concluído"
        if pd.notnull(row["data_vencimento"]) and row["data_vencimento"] < hoje_pd:
            return "🔴 Atrasado"
        return "🟡 Pendente"

    df_f["Situacao"] = df_f.apply(obter_situacao, axis=1)

    # =====================================================
    # KPIs
    # =====================================================
    c1, c2, c3 = st.columns(3)
    c1.success(f"✅ **Concluídos:** {len(df_f[df_f['status'] == 'Concluído'])}")
    c2.warning(f"⏳ **Pendentes:** {len(df_f[df_f['status'] != 'Concluído'])}")
    c3.error(
        f"💸 **Falta Pagar:** R$ {df_f[(df_f['tipo'] == 'Despesa') & (df_f['status'] != 'Concluído')]['valor'].sum():,.2f}"
    )

    # =====================================================
    # 🔥 ACCORDION RESTAURADO
    # =====================================================
    with st.expander("🏦 Saldo em Tempo Real & Reserva", expanded=True):
        st.info(f"💡 {ajuda_texto}")

        c_l1, c_l2, c_l3 = st.columns(3)

        c_l1.metric("💰 Saldo em Contas (Hoje)", f"R$ {saldo_atual_contas:,.2f}")
        c_l2.metric("📊 Balanço do Mês", f"R$ {balanco_mensal:,.2f}")

        cor_delta = "normal" if saldo_exibicao >= 0 else "inverse"
        c_l3.metric(
            label_status,
            f"R$ {saldo_exibicao:,.2f}",
            delta="Impacto acumulado",
            delta_color=cor_delta,
        )

    st.divider()

    # =====================================================
    # CONFIGURAÇÃO DAS COLUNAS
    # =====================================================
    config_colunas = {
        "🗑️": st.column_config.CheckboxColumn("Excluir", default=False),
        "Situacao": st.column_config.SelectboxColumn(
            "Status",
            options=["🟢 Concluído", "🟡 Pendente", "🔴 Atrasado"],
            width=120,
        ),
        "data_vencimento": st.column_config.DateColumn(
            "Vencimento", format="DD/MM/YYYY"
        ),
        "categoria": st.column_config.TextColumn("Categoria"),
        "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
        "descricao": st.column_config.TextColumn("Descrição"),
    }

    colunas_visuais = [
        "🗑️",
        "Situacao",
        "data_vencimento",
        "descricao",
        "categoria",
        "valor",
    ]

    # =====================================================
    # TABELAS (RECEITAS / DESPESAS)
    # =====================================================
    for tipo, label, icon in [
        ("Receita", "Receitas", "💰"),
        ("Despesa", "Despesas", "💸"),
    ]:
        df_tipo = df_f[df_f["tipo"] == tipo].copy()
        total_tipo = total_receitas_mes if tipo == "Receita" else total_despesas_mes

        with st.expander(
                f"{icon} {label} — Total: R$ {total_tipo:,.2f}",
                expanded=True,
        ):
            if df_tipo.empty:
                st.info(f"Nenhuma {tipo.lower()} registrada.")
                continue

            df_tipo["__id__"] = df_tipo.index.astype(str)
            df_tipo["🗑️"] = False

            editor_key = f"editor_{tipo.lower()}"

            df_editado = st.data_editor(
                df_tipo[colunas_visuais],
                hide_index=True,
                use_container_width=True,
                column_config=config_colunas,
                key=editor_key,
            )

            for idx, row in df_tipo.iterrows():
                rid = row["__id__"]
                st.session_state.lixeira_estado[rid] = bool(
                    df_editado.loc[
                        df_editado.index == idx, "🗑️"
                    ].values[0]
                )

            itens_excluir = [
                int(k)
                for k, v in st.session_state.lixeira_estado.items()
                if v and int(k) in df_tipo.index
            ]

            if itens_excluir:
                if st.button(
                        f"🗑️ Remover {len(itens_excluir)} selecionado(s)",
                        key=f"btn_del_{tipo}",
                ):
                    st.session_state.df = st.session_state.df.drop(itens_excluir)
                    st.session_state.lixeira_estado = {}
                    Database.salvar_dados(st.session_state.df)
                    st.rerun()

