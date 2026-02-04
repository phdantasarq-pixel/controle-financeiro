import streamlit as st
from datetime import date, datetime
import pandas as pd
import json

# Imports de serviço e componentes
try:
    from services.ia_service import IAService
    from services.database import Database
    from ui.components import seletor_meses_inteligente
except Exception as e:
    st.error(f"Erro ao carregar dependências: {e}")


def lancamentos_page(df_atual):
    st.header("➕ Gerenciar Lançamentos")

    LISTA_CATEGORIAS = ["Moradia", "Alimentação", "Transporte", "Lazer", "Saúde", "Educação",
                        "Assinaturas", "Salário", "Investimentos", "Cartão de Crédito",
                        "Empréstimo", "Internet", "Outro"]

    # --- [H10] SELETOR DE MÊS ---
    mes_ref = seletor_meses_inteligente(key_suffix="pg_lanc_ia")
    m_sel, a_sel = map(int, mes_ref.split("/"))
    data_selecionada = datetime(a_sel, m_sel, 1)

    try:
        ia = IAService()
    except:
        ia = None

    # --- ABAS DE ENTRADA (MANTIDAS INTEGRALMENTE) ---
    tab_manual, tab_ia = st.tabs(["📝 Lançamento Manual", "🤖 Importar Fatura (IA)"])

    with tab_manual:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                data_base = st.date_input("Vencimento", value=data_selecionada, format="DD/MM/YYYY")
                tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
                valor = st.number_input("Valor R$", min_value=0.0, step=0.01, format="%.2f")
            with c2:
                natureza = st.selectbox("Natureza", ["Fixo", "Variável"])
                categoria = st.selectbox("Categoria", options=LISTA_CATEGORIAS)

            descricao = st.text_input("Descrição")

            if st.button("🚀 Salvar Registro", use_container_width=True):
                if not descricao or valor <= 0:
                    st.error("Preencha descrição e valor.")
                else:
                    novo_dado = pd.DataFrame([{
                        "data_vencimento": pd.to_datetime(data_base),
                        "data_registro": datetime.now().strftime('%Y-%m-%d'),
                        "tipo": tipo,
                        "natureza": natureza,
                        "valor": round(float(valor), 2),
                        "categoria": categoria,
                        "descricao": descricao,
                        "status": "🟡 Pendente",
                        "detalhes": None
                    }])
                    st.session_state.df = pd.concat([st.session_state.df, novo_dado], ignore_index=True)
                    Database.salvar_dados(st.session_state.df)
                    st.success("Salvo com sucesso!")
                    st.rerun()

    with tab_ia:
        st.subheader("🤖 Importação Gemini")
        if ia is None:
            st.warning("IA não configurada.")
        else:
            arquivo = st.file_uploader("Subir Fatura", type=["pdf", "png", "jpg", "jpeg"])
            if arquivo and st.button("✨ Analisar Fatura com Gemini"):
                with st.spinner("Analisando..."):
                    resultado = ia.processar_fatura(arquivo)
                    if resultado and resultado.get("itens"):
                        st.session_state.preview_fatura = resultado
                        st.rerun()

            if "preview_fatura" in st.session_state:
                dados_ia = st.session_state.preview_fatura
                emissor = dados_ia.get("emissor", "Cartão")
                itens = dados_ia.get("itens", [])
                venc_ia = dados_ia.get("vencimento")
                data_final_vencimento = pd.to_datetime(venc_ia) if venc_ia else pd.to_datetime(data_selecionada)

                df_p = pd.DataFrame(itens)
                total_f = df_p['valor'].sum()
                nome_f = f"Fatura {emissor} - {data_final_vencimento.strftime('%m/%y')}"

                with st.container(border=True):
                    st.markdown(f"#### {nome_f}")
                    st.metric("Total", f"R$ {total_f:,.2f}")

                if st.button("📥 Confirmar e Gerar Fatura", use_container_width=True, type="primary"):
                    novo_reg = pd.DataFrame([{
                        "data_vencimento": data_final_vencimento,
                        "data_registro": datetime.now().strftime('%Y-%m-%d'),
                        "tipo": "Despesa",
                        "natureza": "Variável",
                        "valor": round(float(total_f), 2),
                        "categoria": "Cartão de Crédito",
                        "descricao": nome_f,
                        "status": "🟡 Pendente",
                        "detalhes": json.dumps(itens)
                    }])
                    st.session_state.df = pd.concat([st.session_state.df, novo_reg], ignore_index=True)
                    Database.salvar_dados(st.session_state.df)
                    del st.session_state.preview_fatura
                    st.rerun()

    # =====================================================
    # SEÇÃO DE LISTAGEM: ACORDIONS + TABELAS (HOMOLOGADO)
    # =====================================================
    st.divider()
    st.subheader(f"📋 Lançamentos de {mes_ref}")

    if df_atual.empty:
        st.info("Nenhum dado cadastrado.")
        return

    df_temp = df_atual.copy()
    df_temp['data_vencimento'] = pd.to_datetime(df_temp['data_vencimento'], errors='coerce')

    if "status" not in df_temp.columns: df_temp["status"] = "🟡 Pendente"
    if "natureza" not in df_temp.columns: df_temp["natureza"] = "Variável"

    mask = (df_temp['data_vencimento'].dt.month == m_sel) & (df_temp['data_vencimento'].dt.year == a_sel)
    df_mes = df_temp[mask].copy()

    hoje_pd = pd.Timestamp(datetime.now().date())

    config_colunas = {
        "🗑️": st.column_config.CheckboxColumn("Excluir", default=False),
        "Situacao": st.column_config.SelectboxColumn("Status", options=["🟢 Concluído", "🟡 Pendente", "🔴 Atrasado"], width=130),
        "natureza": st.column_config.SelectboxColumn("Natureza", options=["Fixo", "Variável"], width=110),
        "data_vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
        "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
        "categoria": st.column_config.SelectboxColumn("Categoria", options=LISTA_CATEGORIAS)
    }

    for tipo, label, icon in [("Receita", "Receitas", "💰"), ("Despesa", "Despesas", "💸")]:
        df_tipo = df_mes[df_mes["tipo"] == tipo].copy()

        with st.expander(f"{icon} {label} — Total: R$ {df_tipo['valor'].sum():,.2f}", expanded=True):
            if df_tipo.empty:
                st.info(f"Nenhuma {tipo.lower()} no mês.")
                continue

            def aplicar_emoji(row):
                st_bruto = str(row["status"])
                if "Concluído" in st_bruto: return "🟢 Concluído"
                if pd.notnull(row["data_vencimento"]) and row["data_vencimento"] < hoje_pd: return "🔴 Atrasado"
                return "🟡 Pendente"

            df_tipo["Situacao"] = df_tipo.apply(aplicar_emoji, axis=1)
            df_tipo["original_index"] = df_tipo.index
            df_tipo["🗑️"] = False

            cols_view = ["Situacao", "data_vencimento", "descricao", "categoria", "natureza", "valor", "🗑️"]

            df_editado = st.data_editor(
                df_tipo[cols_view + ["original_index"]],
                hide_index=True,
                use_container_width=True,
                column_config={**config_colunas, "original_index": None},
                key=f"editor_lanc_{tipo}_{mes_ref}"
            )

            if df_editado is not None:
                itens_excluir = df_editado[df_editado["🗑️"] == True]["original_index"].tolist()
                if itens_excluir:
                    if st.button(f"🗑️ Confirmar Exclusão ({len(itens_excluir)})", key=f"btn_del_{tipo}_{mes_ref}"):
                        st.session_state.df = st.session_state.df.drop(itens_excluir)
                        Database.salvar_dados(st.session_state.df)
                        st.rerun()
                else:
                    colunas_comp = ["Situacao", "data_vencimento", "descricao", "categoria", "natureza", "valor"]
                    if not df_editado[colunas_comp].equals(df_tipo[colunas_comp]):
                        for _, row_ed in df_editado.iterrows():
                            idx_orig = row_ed["original_index"]
                            st.session_state.df.at[idx_orig, "status"] = row_ed["Situacao"]
                            st.session_state.df.at[idx_orig, "valor"] = row_ed["valor"]
                            st.session_state.df.at[idx_orig, "data_vencimento"] = row_ed["data_vencimento"]
                            st.session_state.df.at[idx_orig, "descricao"] = row_ed["descricao"]
                            st.session_state.df.at[idx_orig, "categoria"] = row_ed["categoria"]
                            st.session_state.df.at[idx_orig, "natureza"] = row_ed["natureza"]
                        Database.salvar_dados(st.session_state.df)
                        st.rerun()

            # --- [H8.1] EDIÇÃO DOS DETALHES DE IA (EXPANDER INTERNO CORRIGIDO) ---
            df_com_detalhes = df_tipo[df_tipo['detalhes'].notna()]
            if not df_com_detalhes.empty:
                with st.expander("🔍 Detalhes das Faturas (Itens da IA)"):
                    st.info("Ajuste abaixo as categorias caso a IA não tenha identificado corretamente.")
                    for idx_fatura, row_det in df_com_detalhes.iterrows():
                        try:
                            itens_ia = json.loads(row_det['detalhes']) if isinstance(row_det['detalhes'], str) else row_det['detalhes']
                            if itens_ia:
                                st.markdown(f"**📍 {row_det['descricao']}**")
                                df_itens_ia = pd.DataFrame(itens_ia)

                                # Editor focado: bloqueia tudo, libera apenas Categoria
                                df_itens_editado = st.data_editor(
                                    df_itens_ia,
                                    hide_index=True,
                                    use_container_width=True,
                                    key=f"edit_ia_{idx_fatura}_{mes_ref}",
                                    column_config={
                                        "valor": st.column_config.NumberColumn("Valor", disabled=True, format="R$ %.2f"),
                                        "descricao": st.column_config.TextColumn("Descrição", disabled=True),
                                        "item": st.column_config.TextColumn("Item", disabled=True),
                                        "categoria": st.column_config.SelectboxColumn(
                                            "Categoria",
                                            options=LISTA_CATEGORIAS,
                                            required=True
                                        )
                                    }
                                )

                                # Se houver mudança na categoria interna, salva no JSON da fatura pai
                                if not df_itens_editado.equals(df_itens_ia):
                                    novos_detalhes = df_itens_editado.to_dict(orient='records')
                                    st.session_state.df.at[idx_fatura, "detalhes"] = json.dumps(novos_detalhes)
                                    Database.salvar_dados(st.session_state.df)
                                    st.rerun()
                        except:
                            continue