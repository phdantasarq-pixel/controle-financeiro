import streamlit as st
import pandas as pd
from ui.components import seletor_meses_inteligente
from services.database import Database
from datetime import datetime


def resumo_page(df: pd.DataFrame):
    st.header("📊 Resumo de Lançamentos")

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
    # PREPARAÇÃO DOS DADOS
    # =====================================================
    df_p = df.copy()
    df_p["data_vencimento"] = pd.to_datetime(df_p["data_vencimento"], errors="coerce")

    if "status" not in df_p.columns:
        df_p["status"] = "🟡 Pendente"

    if "natureza" not in df_p.columns:
        df_p["natureza"] = "Variável"

    def limpa_status(s):
        s = str(s)
        if "Concluído" in s: return "Concluído"
        if "Atrasado" in s: return "Atrasado"
        return "Pendente"

    # =====================================================
    # FILTRO DO MÊS SELECIONADO PARA EXIBIÇÃO
    # =====================================================
    mask = (df_p["data_vencimento"].dt.month == m_sel) & (df_p["data_vencimento"].dt.year == a_sel)
    df_f = df_p[mask].copy()

    hoje_pd = pd.Timestamp(hoje.date())

    def aplicar_emoji(row):
        st_limpo = limpa_status(row["status"])
        if st_limpo == "Concluído": return "🟢 Concluído"
        if pd.notnull(row["data_vencimento"]) and row["data_vencimento"] < hoje_pd: return "🔴 Atrasado"
        return "🟡 Pendente"

    df_f["Situacao"] = df_f.apply(aplicar_emoji, axis=1)

    # Nota: Accordion de Saldo e Reserva removido conforme solicitação.
    st.divider()

    # =====================================================
    # TABELAS COM EDITOR (SALVAMENTO REATIVO + EXCLUSÃO)
    # =====================================================
    config_colunas = {
        "🗑️": st.column_config.CheckboxColumn("Excluir", default=False),
        "Situacao": st.column_config.SelectboxColumn(
            "Status", options=["🟢 Concluído", "🟡 Pendente", "🔴 Atrasado"], width=130
        ),
        "natureza": st.column_config.SelectboxColumn(
            "Natureza", options=["Fixo", "Variável"], width=110
        ),
        "data_vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
        "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
    }

    for tipo, label, icon in [("Receita", "Receitas", "💰"), ("Despesa", "Despesas", "💸")]:
        df_tipo = df_f[df_f["tipo"] == tipo].copy()

        with st.expander(f"{icon} {label} — Total: R$ {df_tipo['valor'].sum():,.2f}", expanded=True):
            if df_tipo.empty:
                st.info(f"Nenhuma {tipo.lower()} registrada.")
                continue

            df_tipo["original_index"] = df_tipo.index
            df_tipo["🗑️"] = False

            cols_view = ["Situacao", "data_vencimento", "descricao", "categoria", "natureza", "valor", "🗑️"]

            # 1. Renderiza o editor
            df_editado = st.data_editor(
                df_tipo[cols_view + ["original_index"]],
                hide_index=True,
                use_container_width=True,
                column_config={**config_colunas, "original_index": None},
                key=f"editor_{tipo.lower()}_{m_sel}_{a_sel}"
            )

            # 2. Lógica de Exclusão
            if df_editado is not None:
                itens_excluir = df_editado[df_editado["🗑️"] == True]["original_index"].tolist()

                if itens_excluir:
                    if st.button(f"🗑️ Confirmar Exclusão ({len(itens_excluir)})", key=f"btn_del_{tipo}_{m_sel}"):
                        st.session_state.df = st.session_state.df.drop(itens_excluir)
                        Database.salvar_dados(st.session_state.df)
                        st.rerun()

                # 3. Lógica de Autosave (detecta mudanças nos dados)
                else:
                    colunas_dados = ["Situacao", "data_vencimento", "descricao", "categoria", "natureza", "valor"]
                    if not df_editado[colunas_dados].equals(df_tipo[colunas_dados]):
                        for _, row in df_editado.iterrows():
                            idx_orig = row["original_index"]
                            st.session_state.df.at[idx_orig, "status"] = row["Situacao"]
                            st.session_state.df.at[idx_orig, "valor"] = row["valor"]
                            st.session_state.df.at[idx_orig, "data_vencimento"] = row["data_vencimento"]
                            st.session_state.df.at[idx_orig, "descricao"] = row["descricao"]
                            st.session_state.df.at[idx_orig, "categoria"] = row["categoria"]
                            st.session_state.df.at[idx_orig, "natureza"] = row["natureza"]

                        Database.salvar_dados(st.session_state.df)
                        st.rerun()