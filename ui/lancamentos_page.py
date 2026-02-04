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

    for aba_tipo, tipo in zip([tab_despesas, tab_receitas], ["Despesa", "Receita"]):
        with aba_tipo:
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

            with st.form(key=f"form_main_{tipo}_{mes_ref}"):
                df_editado = st.data_editor(
                    df_tipo[["Situacao", "data_vencimento", "descricao", "categoria", "natureza", "valor", "🗑️",
                             "original_index"]],
                    hide_index=True,
                    use_container_width=True,
                    column_config={**config_colunas, "original_index": None},
                    key=f"editor_widget_{tipo}_{mes_ref}"
                )
                if st.form_submit_button(f"💾 Salvar Alterações em {tipo}s", use_container_width=True, type="primary"):
                    itens_excluir = df_editado[df_editado["🗑️"] == True]["original_index"].tolist()
                    if itens_excluir:
                        st.session_state.df = st.session_state.df.drop(itens_excluir)

                    for _, row in df_editado.iterrows():
                        idx = row["original_index"]
                        if idx not in itens_excluir:
                            st.session_state.df.loc[
                                idx, ["status", "data_vencimento", "descricao", "categoria", "natureza", "valor"]] = \
                                [row["Situacao"], pd.to_datetime(row["data_vencimento"]), row["descricao"],
                                 row["categoria"], row["natureza"], row["valor"]]

                    Database.salvar_dados(st.session_state.df)
                    st.rerun()

            # --- [DETALHAMENTO IA EM ABAS] ---
            if tipo == "Despesa":
                df_ia = df_tipo[df_tipo['detalhes'].notna() & (df_tipo['detalhes'] != "")]
                if not df_ia.empty:
                    st.markdown("---")
                    st.subheader("🔍 Detalhamento de Itens das Faturas (IA)")

                    # Transformando os expanders em ABAS novamente
                    nomes_abas = [f"📄 {row['descricao'][:20]}" for _, row in df_ia.iterrows()]
                    abas_faturas = st.tabs(nomes_abas)

                    for i, (idx_orig, row_f) in enumerate(df_ia.iterrows()):
                        with abas_faturas[i]:
                            dado_atual = st.session_state.df.at[idx_orig, "detalhes"]
                            df_itens_ia = pd.DataFrame(
                                json.loads(dado_atual) if isinstance(dado_atual, str) else dado_atual)
                            if "parcela" not in df_itens_ia.columns: df_itens_ia["parcela"] = ""

                            with st.form(key=f"form_ia_aba_{idx_orig}"):
                                st.write(f"**Fatura:** {row_f['descricao']} | **Total:** R$ {row_f['valor']:,.2f}")

                                ed_ia = st.data_editor(
                                    df_itens_ia,
                                    hide_index=True,
                                    use_container_width=True,
                                    column_order=["descricao", "valor", "parcela", "categoria"],
                                    column_config={
                                        "valor": st.column_config.NumberColumn("Valor", disabled=True,
                                                                               format="R$ %.2f"),
                                        "descricao": st.column_config.TextColumn("Item", disabled=True),
                                        "parcela": st.column_config.TextColumn("Parcela", disabled=True),
                                        "categoria": st.column_config.SelectboxColumn("Categoria",
                                                                                      options=LISTA_CATEGORIAS,
                                                                                      required=True)
                                    },
                                    key=f"widget_ia_tab_editor_{idx_orig}"
                                )

                                c_save_ia, c_del_ia = st.columns([1, 1])
                                with c_save_ia:
                                    if st.form_submit_button("💾 Salvar Itens", use_container_width=True,
                                                             type="primary"):
                                        st.session_state.df.at[idx_orig, "detalhes"] = json.dumps(
                                            ed_ia.to_dict('records'))
                                        Database.salvar_dados(st.session_state.df)
                                        st.toast(f"✅ Itens de {row_f['descricao']} salvos!")
                                        st.rerun()
                                with c_del_ia:
                                    if st.form_submit_button("🗑️ Apagar Fatura", use_container_width=True):
                                        st.session_state.df = st.session_state.df.drop(idx_orig)
                                        Database.salvar_dados(st.session_state.df)
                                        st.rerun()