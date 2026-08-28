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
    # --- CSS REFINADO (LUXURY & ALTO CONTRASTE) ---
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

            .main-header { 
                font-family: 'Inter', sans-serif; 
                padding: 15px 0 10px 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                margin-bottom: 25px; 
            }
            .title-main {
                font-size: 2.2rem; font-weight: 800; letter-spacing: -1px;
                color: #ffffff !important;
                margin-bottom: 0px; text-transform: uppercase;
            }
            .subtitle-main {
                font-size: 0.85rem; font-weight: 600; color: #38bdf8 !important;
                letter-spacing: 2px; text-transform: uppercase;
            }
            .stForm {
                border: 1px solid rgba(255, 255, 255, 0.12) !important;
                background: #151d2e !important;
                border-radius: 16px !important;
                padding: 20px !important;
            }
            .ia-section-card {
                background: #151d2e;
                border-radius: 14px; padding: 18px;
                border: 1px solid rgba(56, 189, 248, 0.25); margin: 12px 0;
            }

            /* Estilo dos Cartões Mobile de Lançamentos */
            .item-card {
                background: #151d2e;
                border-radius: 14px;
                padding: 14px 18px;
                margin-bottom: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
            }
            .item-card-ok { border-left: 5px solid #22c55e; }
            .item-card-pendente { border-left: 5px solid #eab308; }
            .item-card-atrasado { border-left: 5px solid #ef4444; }

            .item-badge {
                font-size: 0.75rem;
                font-weight: 700;
                padding: 3px 8px;
                border-radius: 6px;
                display: inline-block;
                margin-right: 6px;
            }
            .badge-cat { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
            .badge-nat { background: rgba(255, 255, 255, 0.08); color: #cbd5e1; }
        </style>

        <div class="main-header">
            <div class="subtitle-main">Cockpit de Entradas</div>
            <div class="title-main">Gerenciar Lançamentos</div>
            <div class="subtitle-main" style="color: #94a3b8 !important; letter-spacing: 1px; margin-top: 4px;">
                PlanejAI <span style="color: #38bdf8; font-weight: bold;">v1.0</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    LISTA_CATEGORIAS = [
        "Alimentação", "Assinaturas", "Beleza/Estética", "Cartão de Crédito",
        "Educação", "Empréstimo", "Estilo de Vida", "Investimentos",
        "Internet/TV", "Lazer", "Moradia", "Outro", "Pet", "Presentes",
        "Salário", "Saúde", "Transporte", "Vestuário", "Viagem"
    ]
    OPCOES_NATUREZA = ["Fixo", "Variável"]

    # --- SELETOR DE MÊS ---
    mes_ref = seletor_meses_inteligente(key_suffix="pg_lanc_ia")
    m_sel, a_sel = map(int, mes_ref.split("/"))
    data_selecionada = datetime(a_sel, m_sel, 1)

    try:
        ia = IAService()
    except:
        ia = None

    # --- ENTRADA DE DADOS ---
    tab_manual, tab_ia = st.tabs(["📝 Lançamento Manual", "🤖 Importar Fatura (IA)"])

    with tab_manual:
        with st.container(border=True):
            st.markdown('<p style="font-weight:700; font-size:1.1rem; margin-bottom:15px; color:#ffffff;">Novo Registro</p>',
                        unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                tipo_manual = st.selectbox("Tipo", ["Despesa", "Receita"], key="sel_tipo_manual")
                natureza = st.selectbox("Natureza", OPCOES_NATUREZA, key="sel_nat_manual")
                valor = st.number_input("Valor R$", min_value=0.0, step=0.01, format="%.2f")
            with c2:
                categoria = st.selectbox("Categoria", options=LISTA_CATEGORIAS, key="sel_cat_manual")
                data_base = st.date_input("Vencimento", value=data_selecionada, format="DD/MM/YYYY")
                parcela_input = st.text_input("Parcela", placeholder="Ex: 1/12", key="in_parc_manual")

            descricao = st.text_input("Descrição", placeholder="Ex: Aluguel Fevereiro", key="in_desc_manual")

            if st.button("🚀 Salvar Lançamento", use_container_width=True, type="primary"):
                if not descricao or valor <= 0:
                    st.error("Preencha descrição e valor.")
                else:
                    novo_dado = pd.DataFrame([{
                        "data_vencimento": pd.to_datetime(data_base),
                        "data_registro": datetime.now().strftime('%Y-%m-%d'),
                        "tipo": tipo_manual,
                        "natureza": natureza,
                        "valor": round(float(valor), 2),
                        "categoria": categoria,
                        "descricao": descricao,
                        "status": "🟡 Pendente",
                        "detalhes": None,
                        "parcela": parcela_input
                    }])

                    st.session_state.df = pd.concat([st.session_state.df, novo_dado], ignore_index=True)
                    Database.salvar_dados(st.session_state.df)

                    if 'dados_detalhados' in st.session_state:
                        del st.session_state.dados_detalhados

                    st.session_state.form_version += 1
                    st.toast("Lançamento salvo com sucesso!", icon="✅")
                    st.rerun()

    with tab_ia:
        st.markdown(
            '<p class="subtitle-main" style="color:#fff !important; font-size:1rem; margin-bottom:15px;">🔍 Detalhamento de Itens das Faturas (IA)</p>',
            unsafe_allow_html=True)

        if ia is None:
            st.warning("IA não configurada.")
        else:
            if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
            arquivo = st.file_uploader("Upload de Fatura", type=["pdf", "png", "jpg", "jpeg", "csv"],
                                       key=f"up_{st.session_state.uploader_key}")

            if arquivo:
                if st.button("✨ Analisar Fatura com Gemini", use_container_width=True, type="primary"):
                    with st.spinner("IA processando..."):
                        resultado = ia.processar_texto(
                            f"Extraia os gastos deste CSV: {arquivo.getvalue().decode('utf-8')}") if arquivo.name.lower().endswith(
                            '.csv') else ia.processar_fatura(arquivo)
                        if resultado and resultado.get("itens"):
                            for item in resultado["itens"]:
                                item["excluir"] = False
                                if not item.get("natureza"): item["natureza"] = "Variável"
                                if not item.get("categoria"): item["categoria"] = "Outro"
                            st.session_state.preview_fatura = resultado
                            st.rerun()

            if "preview_fatura" in st.session_state:
                st.markdown('<div class="ia-section-card">', unsafe_allow_html=True)
                dados_ia = st.session_state.preview_fatura
                emissor = dados_ia.get("emissor", "Cartão")
                st.write(f"### Conferência: {emissor}")

                df_ia_display = pd.DataFrame(dados_ia["itens"]).fillna("")
                cols = [c for c in df_ia_display.columns if c != 'excluir'] + ['excluir']
                df_ia_display = df_ia_display[cols]

                df_editavel = st.data_editor(
                    df_ia_display,
                    column_config={
                        "descricao": st.column_config.TextColumn("Descrição", disabled=True),
                        "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f", disabled=True),
                        "categoria": st.column_config.SelectboxColumn("Categoria", options=LISTA_CATEGORIAS,
                                                                      required=True),
                        "natureza": st.column_config.SelectboxColumn("Natureza", options=OPCOES_NATUREZA,
                                                                     required=True),
                        "excluir": st.column_config.CheckboxColumn("🗑️", default=False)
                    },
                    hide_index=True, use_container_width=True, key="editor_ia_main"
                )

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("📥 Importar Tudo", use_container_width=True, type="primary"):
                        df_final = df_editavel[df_editavel["excluir"] == False].copy()
                        venc_ia = dados_ia.get("vencimento")
                        dt_venc = pd.to_datetime(venc_ia) if venc_ia else pd.to_datetime(data_selecionada)

                        novo_reg = pd.DataFrame([{
                            "data_vencimento": dt_venc,
                            "data_registro": datetime.now().strftime('%Y-%m-%d'),
                            "tipo": "Despesa", "natureza": "Variável",
                            "valor": round(float(df_final['valor'].sum()), 2),
                            "categoria": "Cartão de Crédito", "descricao": f"Fatura {emissor}",
                            "status": "🟡 Pendente",
                            "detalhes": json.dumps(df_final.drop(columns=["excluir"]).to_dict('records')),
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
                st.markdown('</div>', unsafe_allow_html=True)

    # --- LISTAGEM ---
    st.divider()
    df_temp = df_atual.copy()
    df_temp['data_vencimento'] = pd.to_datetime(df_temp['data_vencimento'], errors='coerce')
    mask = (df_temp['data_vencimento'].dt.month == m_sel) & (df_temp['data_vencimento'].dt.year == a_sel)
    df_mes = df_temp[mask].copy()
    hoje_pd = pd.Timestamp(datetime.now().date())

    # --- SELETOR DE MODO DE EXIBIÇÃO (HÍBRIDO MOBILE/DESKTOP) ---
    col_titulo_tab, col_modo = st.columns([1.5, 1])
    with col_titulo_tab:
        st.subheader("📋 Meus Lançamentos")
    with col_modo:
        modo_visao = st.radio(
            "Modo de Exibição",
            ["📱 Cartões (Mobile)", "📊 Tabela Clássica"],
            horizontal=True,
            label_visibility="collapsed",
            key="modo_visao_lancamentos"
        )

    tab_despesas, tab_receitas = st.tabs(["💸 Despesas", "💰 Receitas"])

    for aba_tipo, tipo in zip([tab_despesas, tab_receitas], ["Despesa", "Receita"]):
        with aba_tipo:
            df_tipo = df_mes[df_mes["tipo"] == tipo].copy()
            if df_tipo.empty:
                st.info(f"Nenhuma {tipo.lower()} para este mês.")
                continue

            df_tipo["Situacao"] = df_tipo.apply(lambda r: "🟢 Concluído" if "Concluído" in str(r["status"]) else (
                "🔴 Atrasado" if pd.notnull(r["data_vencimento"]) and r["data_vencimento"] < hoje_pd else "🟡 Pendente"),
                                                axis=1)
            df_tipo["original_index"] = df_tipo.index

            # --- MODO 1: CARTÕES INTERATIVOS (MOBILE FRIENDLY) ---
            if modo_visao == "📱 Cartões (Mobile)":
                cor_valor = "#f87171" if tipo == "Despesa" else "#4ade80"
                sinal = "-" if tipo == "Despesa" else "+"

                # Busca rápida para filtrar itens
                col_busca, col_filtro = st.columns([1.8, 1.2])
                with col_busca:
                    busca = st.text_input("🔍 Buscar", placeholder="Ex: Mercado, Aluguel...", key=f"busca_{tipo}")
                with col_filtro:
                    status_filtro = st.selectbox("Status", ["Todos", "🟢 Concluído", "🟡 Pendente", "🔴 Atrasado"], key=f"filtro_{tipo}")

                df_cards = df_tipo.copy()
                if busca:
                    df_cards = df_cards[df_cards['descricao'].str.contains(busca, case=False, na=False) |
                                        df_cards['categoria'].str.contains(busca, case=False, na=False)]
                if status_filtro != "Todos":
                    df_cards = df_cards[df_cards['Situacao'] == status_filtro]

                if df_cards.empty:
                    st.info("Nenhum lançamento encontrado com os filtros aplicados.")
                else:
                    for _, row in df_cards.iterrows():
                        idx = row["original_index"]
                        sit = row["Situacao"]
                        classe_borda = "item-card-ok" if "🟢" in sit else ("item-card-atrasado" if "🔴" in sit else "item-card-pendente")
                        dt_formatada = row["data_vencimento"].strftime('%d/%m/%Y') if pd.notnull(row["data_vencimento"]) else "Sem data"
                        parcela_str = f" • Parcela {row['parcela']}" if pd.notnull(row.get('parcela')) and row.get('parcela') != "" else ""

                        # Card Visual
                        st.markdown(f"""
                            <div class="item-card {classe_borda}">
                                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                                    <div>
                                        <span class="item-badge badge-cat">{row['categoria']}</span>
                                        <span class="item-badge badge-nat">{row['natureza']}</span>
                                    </div>
                                    <div style="font-size: 1.15rem; font-weight: 800; color: {cor_valor};">
                                        {sinal} R$ {row['valor']:,.2f}
                                    </div>
                                </div>
                                <div style="font-size: 1.05rem; font-weight: 700; color: #ffffff; margin-bottom: 4px;">
                                    {row['descricao']}
                                </div>
                                <div style="font-size: 0.8rem; color: #94a3b8;">
                                    📅 Vencimento: {dt_formatada} {parcela_str} | <b>{sit}</b>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                        # Ações Rápidas do Cartão
                        c_acao1, c_acao2, c_acao3 = st.columns([1.5, 1.2, 1])

                        # 1. Toggle rápido de status (Concluir / Reabrir)
                        with c_acao1:
                            if "🟢" in sit:
                                if st.button("⏳ Reabrir", key=f"btn_reabrir_{idx}", use_container_width=True):
                                    st.session_state.df.loc[idx, "status"] = "🟡 Pendente"
                                    Database.salvar_dados(st.session_state.df)
                                    st.rerun()
                            else:
                                if st.button("✅ Concluir", key=f"btn_concluir_{idx}", type="primary", use_container_width=True):
                                    st.session_state.df.loc[idx, "status"] = "🟢 Concluído"
                                    Database.salvar_dados(st.session_state.df)
                                    st.rerun()

                        # 2. Edição rápida expansível
                        with c_acao2:
                            with st.popover("✏️ Editar", use_container_width=True):
                                st.markdown(f"**Editar: {row['descricao']}**")
                                ed_desc = st.text_input("Descrição", value=row["descricao"], key=f"ed_desc_{idx}")
                                ed_val = st.number_input("Valor (R$)", value=float(row["valor"]), min_value=0.0, step=1.0, format="%.2f", key=f"ed_val_{idx}")
                                ed_cat = st.selectbox("Categoria", options=LISTA_CATEGORIAS, index=LISTA_CATEGORIAS.index(row["categoria"]) if row["categoria"] in LISTA_CATEGORIAS else 0, key=f"ed_cat_{idx}")
                                ed_nat = st.selectbox("Natureza", options=OPCOES_NATUREZA, index=OPCOES_NATUREZA.index(row["natureza"]) if row["natureza"] in OPCOES_NATUREZA else 0, key=f"ed_nat_{idx}")
                                ed_dt = st.date_input("Vencimento", value=row["data_vencimento"].to_pydatetime() if pd.notnull(row["data_vencimento"]) else data_selecionada, format="DD/MM/YYYY", key=f"ed_dt_{idx}")

                                if st.button("💾 Salvar Alterações", key=f"btn_save_card_{idx}", type="primary", use_container_width=True):
                                    st.session_state.df.loc[idx, ["descricao", "valor", "categoria", "natureza", "data_vencimento"]] = [
                                        ed_desc, round(float(ed_val), 2), ed_cat, ed_nat, pd.to_datetime(ed_dt)
                                    ]
                                    Database.salvar_dados(st.session_state.df)
                                    st.toast("Lançamento atualizado!", icon="💾")
                                    st.rerun()

                        # 3. Excluir item
                        with c_acao3:
                            if st.button("🗑️", key=f"btn_del_card_{idx}", use_container_width=True, help="Excluir este lançamento"):
                                st.session_state.df = st.session_state.df.drop(idx)
                                Database.salvar_dados(st.session_state.df)
                                st.toast("Lançamento removido!", icon="🗑️")
                                st.rerun()

                        st.write("")

            # --- MODO 2: TABELA CLÁSSICA (DATA EDITOR) ---
            else:
                df_tipo["🗑️"] = False
                with st.form(key=f"form_v8_{tipo}"):
                    df_editado = st.data_editor(
                        df_tipo[["Situacao", "data_vencimento", "descricao", "natureza", "categoria", "valor", "🗑️",
                                 "original_index"]].fillna(""),
                        hide_index=True, use_container_width=True,
                        column_config={
                            "Situacao": st.column_config.SelectboxColumn("Status", options=["🟢 Concluído", "🟡 Pendente",
                                                                                            "🔴 Atrasado"]),
                            "data_vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
                            "natureza": st.column_config.SelectboxColumn("Natureza", options=OPCOES_NATUREZA),
                            "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                            "categoria": st.column_config.SelectboxColumn("Categoria", options=LISTA_CATEGORIAS),
                            "🗑️": st.column_config.CheckboxColumn("🗑️", default=False),
                            "original_index": None
                        },
                        key=f"editor_{tipo}"
                    )

                    salvar = st.form_submit_button("💾 Salvar Alterações na Lista", use_container_width=True, type="primary")

                    if salvar:
                        itens_excluir = df_editado[df_editado["🗑️"] == True]["original_index"].tolist()
                        if itens_excluir:
                            st.session_state.df = st.session_state.df.drop(itens_excluir)

                        for _, row in df_editado.iterrows():
                            idx = row["original_index"]
                            if idx not in itens_excluir:
                                st.session_state.df.loc[
                                    idx, ["status", "data_vencimento", "descricao", "natureza", "categoria", "valor"]] = \
                                    [row["Situacao"], pd.to_datetime(row["data_vencimento"]), row["descricao"],
                                     row["natureza"], row["categoria"], row["valor"]]

                        Database.salvar_dados(st.session_state.df)
                        st.rerun()

            if tipo == "Despesa":
                df_ia = df_tipo[
                    df_tipo['detalhes'].notna() &
                    df_tipo['detalhes'].astype(str).str.startswith('[') &
                    (df_tipo['detalhes'].astype(str) != "[]")
                    ]

                if not df_ia.empty:
                    st.write("")
                    st.markdown('### 🔍 Detalhamento de Itens das Faturas (IA)')

                    titulos_abas = [f"📦 {row['descricao']}" for _, row in df_ia.iterrows()]
                    abas_faturas = st.tabs(titulos_abas)

                    for i, (idx_orig, row_f) in enumerate(df_ia.iterrows()):
                        with abas_faturas[i]:
                            dado_atual = st.session_state.df.at[idx_orig, "detalhes"]

                            try:
                                if isinstance(dado_atual, str):
                                    dados_json = json.loads(dado_atual)
                                else:
                                    dados_json = dado_atual

                                if not isinstance(dados_json, list):
                                    dados_json = []
                            except:
                                dados_json = []

                            if dados_json:
                                df_itens_ia = pd.DataFrame(dados_json).fillna("")
                            else:
                                df_itens_ia = pd.DataFrame(columns=["descricao", "valor", "categoria", "natureza"])

                            ed_ia = st.data_editor(
                                df_itens_ia,
                                hide_index=True,
                                use_container_width=True,
                                key=f"ed_ia_{idx_orig}",
                                column_config={
                                    "descricao": st.column_config.TextColumn("Descrição", disabled=True),
                                    "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f", disabled=True),
                                    "categoria": st.column_config.SelectboxColumn("Categoria",
                                                                                  options=LISTA_CATEGORIAS),
                                    "natureza": st.column_config.SelectboxColumn("Natureza", options=OPCOES_NATUREZA)
                                }
                            )

                            col_btn_1, col_btn_2, _ = st.columns([1.5, 1.2, 2])
                            with col_btn_1:
                                if st.button(f"💾 Atualizar Fatura", key=f"btn_ia_{idx_orig}", type="primary",
                                             use_container_width=True):
                                    st.session_state.df.at[idx_orig, "detalhes"] = json.dumps(ed_ia.to_dict('records'))
                                    Database.salvar_dados(st.session_state.df)
                                    st.toast("Fatura atualizada!")
                                    st.rerun()
                            with col_btn_2:
                                if st.button(f"🗑️ Excluir Fatura", key=f"del_fat_{idx_orig}", use_container_width=True):
                                    st.session_state.df = st.session_state.df.drop(idx_orig)
                                    Database.salvar_dados(st.session_state.df)
                                    st.rerun()
