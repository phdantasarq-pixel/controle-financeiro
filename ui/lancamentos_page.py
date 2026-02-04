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

    LISTA_CATEGORIAS = [
        "Alimentação", "Assinaturas", "Beleza/Estética", "Cartão de Crédito",
        "Educação", "Empréstimo", "Estilo de Vida", "Investimentos",
        "Internet/TV", "Lazer", "Moradia", "Outro", "Pet", "Presentes",
        "Salário", "Saúde", "Transporte", "Vestuário", "Viagem"
    ]

    # --- [H10] SELETOR DE MÊS ---
    mes_ref = seletor_meses_inteligente(key_suffix="pg_lanc_ia")
    m_sel, a_sel = map(int, mes_ref.split("/"))
    data_selecionada = datetime(a_sel, m_sel, 1)

    try:
        ia = IAService()
    except:
        ia = None

    # --- ABAS DE ENTRADA (MANUAL / IA) ---
    tab_manual, tab_ia = st.tabs(["📝 Lançamento Manual", "🤖 Importar Fatura (IA)"])

    with tab_manual:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                data_base = st.date_input("Vencimento", value=data_selecionada, format="DD/MM/YYYY")
                tipo_manual = st.selectbox("Tipo", ["Despesa", "Receita"], key="sel_tipo_manual")
            with c2:
                natureza = st.selectbox("Natureza", ["Fixo", "Variável"], key="sel_nat_manual")
                categoria = st.selectbox("Categoria", options=LISTA_CATEGORIAS, key="sel_cat_manual")
            with c3:
                parcela_input = st.text_input("Parcela", placeholder="Ex: 1/12", key="in_parc_manual")

            valor = st.number_input("Valor R$", min_value=0.0, step=0.01, format="%.2f")
            descricao = st.text_input("Descrição", key="in_desc_manual")

            if st.button("🚀 Salvar Registro", use_container_width=True):
                if not descricao or valor <= 0:
                    st.error("Preencha descrição e valor.")
                else:
                    novo_dado = pd.DataFrame([{
                        "data_vencimento": pd.to_datetime(data_base),
                        "data_registro": datetime.now().strftime('%Y-%m-%d'),
                        "tipo": tipo_manual, "natureza": natureza, "valor": round(float(valor), 2),
                        "categoria": categoria, "descricao": descricao,
                        "status": "🟡 Pendente", "detalhes": None, "parcela": parcela_input
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
            if "uploader_key" not in st.session_state:
                st.session_state.uploader_key = 0

            arquivo = st.file_uploader(
                "Subir Fatura",
                type=["pdf", "png", "jpg", "jpeg"],
                key=f"fatura_uploader_{st.session_state.uploader_key}"
            )

            if arquivo and st.button("✨ Analisar Fatura com Gemini"):
                with st.spinner("Analisando..."):
                    resultado = ia.processar_fatura(arquivo)
                    if resultado and resultado.get("itens"):
                        for item in resultado["itens"]:
                            item["excluir"] = False
                        st.session_state.preview_fatura = resultado
                        st.rerun()

            if "preview_fatura" in st.session_state:
                dados_ia = st.session_state.preview_fatura
                emissor = dados_ia.get("emissor", "Cartão")
                itens = dados_ia.get("itens", [])
                venc_ia = dados_ia.get("vencimento")
                data_final_vencimento = pd.to_datetime(venc_ia) if venc_ia else pd.to_datetime(data_selecionada)

                df_p = pd.DataFrame(itens)
                if "parcela" not in df_p.columns: df_p["parcela"] = ""
                if "excluir" not in df_p.columns: df_p["excluir"] = False

                with st.container(border=True):
                    st.markdown(f"#### 🔍 Conferência: Fatura {emissor}")
                    df_editavel = st.data_editor(
                        df_p,
                        column_order=["excluir", "descricao", "valor", "categoria", "parcela"],
                        column_config={
                            "excluir": st.column_config.CheckboxColumn("🗑️", default=False),
                            "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                            "categoria": st.column_config.SelectboxColumn("Categoria", options=LISTA_CATEGORIAS),
                            "parcela": st.column_config.TextColumn("Parcela")
                        },
                        hide_index=True,
                        use_container_width=True,
                        key="editor_pre_importacao"
                    )

                    df_final = df_editavel[df_editavel["excluir"] == False].copy()
                    total_f = df_final['valor'].sum()
                    nome_f = f"Fatura {emissor} - {data_final_vencimento.strftime('%m/%y')}"

                    st.metric("Total a Importar (ajustado)", f"R$ {total_f:,.2f}")

                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("📥 Confirmar e Gerar Fatura", use_container_width=True, type="primary"):
                            df_para_salvar = df_final.drop(columns=["excluir"])
                            novo_reg = pd.DataFrame([{
                                "data_vencimento": data_final_vencimento,
                                "data_registro": datetime.now().strftime('%Y-%m-%d'),
                                "tipo": "Despesa", "natureza": "Variável", "valor": round(float(total_f), 2),
                                "categoria": "Cartão de Crédito", "descricao": nome_f,
                                "status": "🟡 Pendente", "detalhes": json.dumps(df_para_salvar.to_dict('records')),
                                "parcela": ""
                            }])
                            st.session_state.df = pd.concat([st.session_state.df, novo_reg], ignore_index=True)
                            Database.salvar_dados(st.session_state.df)
                            del st.session_state.preview_fatura
                            st.session_state.uploader_key += 1
                            st.rerun()
                    with c2:
                        if st.button("❌ Cancelar", use_container_width=True):
                            del st.session_state.preview_fatura
                            st.rerun()

    # --- LISTAGEM ---
    st.divider()
    st.subheader(f"📋 Lançamentos de {mes_ref}")

    if df_atual.empty:
        st.info("Nenhum dado cadastrado.")
        return

    df_temp = df_atual.copy()
    df_temp['data_vencimento'] = pd.to_datetime(df_temp['data_vencimento'], errors='coerce')
    mask = (df_temp['data_vencimento'].dt.month == m_sel) & (df_temp['data_vencimento'].dt.year == a_sel)
    df_mes = df_temp[mask].copy()
    hoje_pd = pd.Timestamp(datetime.now().date())

    config_colunas = {
        "🗑️": st.column_config.CheckboxColumn("Excluir", default=False),
        "Situacao": st.column_config.SelectboxColumn("Status", options=["🟢 Concluído", "🟡 Pendente", "🔴 Atrasado"],
                                                     width=130),
        "natureza": st.column_config.SelectboxColumn("Natureza", options=["Fixo", "Variável"], width=110),
        "data_vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
        "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
        "categoria": st.column_config.SelectboxColumn("Categoria", options=LISTA_CATEGORIAS)
    }

    tab_despesas, tab_receitas = st.tabs(["💸 Despesas", "💰 Receitas"])

    for aba, tipo in zip([tab_despesas, tab_receitas], ["Despesa", "Receita"]):
        with aba:
            df_tipo = df_mes[df_mes["tipo"] == tipo].copy()
            st.metric(f"Total {tipo}s", f"R$ {df_tipo['valor'].sum():,.2f}")

            if df_tipo.empty:
                st.info(f"Sem {tipo.lower()}s este mês.")
                continue

            df_tipo["Situacao"] = df_tipo.apply(lambda r: "🟢 Concluído" if "Concluído" in str(r["status"]) else (
                "🔴 Atrasado" if pd.notnull(r["data_vencimento"]) and r["data_vencimento"] < hoje_pd else "🟡 Pendente"),
                                                axis=1)
            df_tipo["original_index"] = df_tipo.index
            df_tipo["🗑️"] = False

            # Editor Principal
            df_editado = st.data_editor(
                df_tipo[["Situacao", "data_vencimento", "descricao", "categoria", "natureza", "valor", "🗑️",
                         "original_index"]],
                hide_index=True,
                use_container_width=True,
                column_config={**config_colunas, "original_index": None},
                key=f"editor_principal_{tipo}_{mes_ref}"
            )

            # Processamento de exclusão/edição da tabela principal
            if df_editado is not None:
                itens_excluir = df_editado[df_editado["🗑️"] == True]["original_index"].tolist()
                if itens_excluir:
                    if st.button(f"🗑️ Confirmar Exclusão ({len(itens_excluir)})", key=f"del_btn_{tipo}_{mes_ref}"):
                        st.session_state.df = st.session_state.df.drop(itens_excluir)
                        Database.salvar_dados(st.session_state.df)
                        st.rerun()
                else:
                    cols_comp = ["Situacao", "data_vencimento", "descricao", "categoria", "natureza", "valor"]
                    if not df_editado[cols_comp].equals(df_tipo[cols_comp]):
                        for _, row in df_editado.iterrows():
                            idx = row["original_index"]
                            st.session_state.df.loc[
                                idx, ["status", "data_vencimento", "descricao", "categoria", "natureza", "valor"]] = \
                                [row["Situacao"], row["data_vencimento"], row["descricao"], row["categoria"],
                                 row["natureza"], row["valor"]]
                        Database.salvar_dados(st.session_state.df)

            # --- [DETALHAMENTO IA] ---
            # INDENTAÇÃO CORRIGIDA: Fora do bloco 'if df_editado is not None'
            # --- [DETALHAMENTO IA] ---
            if tipo == "Despesa":
                df_ia = df_tipo[df_tipo['detalhes'].notna() & (df_tipo['detalhes'] != "")]
                if not df_ia.empty:
                    st.markdown("---")
                    st.subheader("🔍 Detalhamento de Itens das Faturas (IA)")

                    abas_faturas = st.tabs([f"📄 {row['descricao'][:20]}" for _, row in df_ia.iterrows()])

                    for i, (idx_orig, row_f) in enumerate(df_ia.iterrows()):
                        with abas_faturas[i]:
                            edit_mode_key = f"edit_mode_{idx_orig}"
                            editor_key = f"editor_ia_widget_{idx_orig}"

                            if edit_mode_key not in st.session_state:
                                st.session_state[edit_mode_key] = False

                            c_info, c_edit, c_del = st.columns([3, 1, 1])
                            with c_info:
                                st.write(f"**Origem:** {row_f['descricao']}")

                            with c_edit:
                                if not st.session_state[edit_mode_key]:
                                    # Botão alterado para deixar claro o objetivo
                                    if st.button("✏️ Ajustar Categorias", key=f"btn_edit_{idx_orig}",
                                                 use_container_width=True):
                                        st.session_state[edit_mode_key] = True
                                        st.rerun()
                                else:
                                    if st.button("💾 Salvar Alterações", key=f"btn_save_{idx_orig}", type="primary",
                                                 use_container_width=True):
                                        if editor_key in st.session_state:
                                            edits = st.session_state[editor_key]
                                            if edits and "edited_rows" in edits:
                                                dado_json = st.session_state.df.at[idx_orig, "detalhes"]
                                                df_itens = pd.DataFrame(
                                                    json.loads(dado_json) if isinstance(dado_json, str) else dado_json)

                                                for r_idx, changes in edits["edited_rows"].items():
                                                    for col, val in changes.items():
                                                        df_itens.at[int(r_idx), col] = val

                                                st.session_state.df.at[idx_orig, "detalhes"] = json.dumps(
                                                    df_itens.to_dict('records'))

                                        st.session_state[edit_mode_key] = False
                                        Database.salvar_dados(st.session_state.df)
                                        st.toast("✅ Categorias atualizadas!", icon="💾")
                                        st.rerun()

                            with c_del:
                                if st.button("🗑️ Apagar Fatura", key=f"btn_del_ia_{idx_orig}",
                                             use_container_width=True):
                                    st.session_state.df = st.session_state.df.drop(idx_orig)
                                    Database.salvar_dados(st.session_state.df)
                                    st.rerun()

                            # Recuperação e Exibição com Colunas Travadas
                            dado_atual = st.session_state.df.at[idx_orig, "detalhes"]
                            df_itens_ia = pd.DataFrame(
                                json.loads(dado_atual) if isinstance(dado_atual, str) else dado_atual)
                            if "parcela" not in df_itens_ia.columns: df_itens_ia["parcela"] = ""

                            # Configuração de colunas: Apenas 'categoria' fica editável
                            config_travada = {
                                "valor": st.column_config.NumberColumn("Valor", disabled=True, format="R$ %.2f"),
                                "descricao": st.column_config.TextColumn("Item", disabled=True),
                                "parcela": st.column_config.TextColumn("Parcela", disabled=True),
                                "categoria": st.column_config.SelectboxColumn("Categoria", options=LISTA_CATEGORIAS,
                                                                              required=True)
                            }

                            if st.session_state[edit_mode_key]:
                                st.data_editor(
                                    df_itens_ia,
                                    hide_index=True,
                                    use_container_width=True,
                                    key=editor_key,
                                    column_order=["descricao", "valor", "parcela", "categoria"],
                                    column_config=config_travada
                                )
                                st.info("💡 Somente a coluna **Categoria** está liberada para edição.")
                            else:
                                st.dataframe(
                                    df_itens_ia,
                                    hide_index=True,
                                    use_container_width=True,
                                    column_order=["descricao", "valor", "parcela", "categoria"]
                                )