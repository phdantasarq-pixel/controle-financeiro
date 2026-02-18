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
    # --- CSS REFINADO (LUXURY & STABLE) ---
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

            .main-header { font-family: 'Inter', sans-serif; margin-bottom: 25px; }
            .title-main {
                font-size: 2rem; font-weight: 800; letter-spacing: -1px;
                background: linear-gradient(90deg, #FFFFFF 0%, #A0A0A0 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                margin-bottom: 0px; text-transform: uppercase;
            }
            .subtitle-main {
                font-size: 0.8rem; font-weight: 300; color: #3498db;
                letter-spacing: 2px; text-transform: uppercase;
            }
            .stForm {
                border: 1px solid rgba(255, 255, 255, 0.05) !important;
                background: rgba(255, 255, 255, 0.01) !important;
                border-radius: 15px !important;
                padding: 20px !important;
            }
            .ia-section-card {
                background: rgba(52, 152, 219, 0.03);
                border-radius: 12px; padding: 15px;
                border: 1px solid rgba(52, 152, 219, 0.1); margin: 10px 0;
            }
        </style>

        <div class="main-header">
            <div class="subtitle-main">Cockpit de Entradas</div>
            <div class="title-main">Gerenciar Lançamentos</div>
            <div class="subtitle-main" style="color: rgba(255,255,255,0.4); letter-spacing: 1px; margin-top: 5px;">
                PlanejAI <span style="color: #3498db; font-weight: bold;">v1.0</span>
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
            st.markdown('<p style="font-weight:600; font-size:1.1rem; margin-bottom:15px;">Novo Registro</p>',
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
                    # 1. Preparação do dado
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

                    # 2. Atualização do estado local
                    st.session_state.df = pd.concat([st.session_state.df, novo_dado], ignore_index=True)

                    # 3. Persistência no MongoDB Atlas (Nuvem)
                    Database.salvar_dados(st.session_state.df)

                    # --- CORREÇÃO DO BUG DE ATUALIZAÇÃO ---
                    # 4. Limpamos qualquer cache de análise que a página de Inteligência Financeira utilize
                    # Se você usa alguma chave específica no session_state para os gráficos, limpe-a aqui.
                    if 'dados_detalhados' in st.session_state:
                        del st.session_state.dados_detalhados

                    # 5. Incrementamos a versão do formulário (Para limpar os campos de input da tela)
                    st.session_state.form_version += 1

                    st.toast("Lançamento salvo com sucesso!", icon="✅")

                    # 6. O rerun agora vai recarregar o Database.carregar_dados()
                    # com os novos valores de data e status, limpando o card de "Atrasados".
                    st.rerun()

    with tab_ia:
        st.markdown(
            '<p class="subtitle-main" style="color:#fff; font-size:1rem; margin-bottom:15px;">🔍 Detalhamento de Itens das Faturas (IA)</p>',
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

                # Limpeza e Ordenação: Natureza e Categoria editáveis, Excluir por último
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
                # Filtra apenas lançamentos que possuem detalhes da IA
                # No ui/lancamentos_page.py, procure a linha do filtro df_ia:
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
                            # Recupera o dado e garante que não seja nulo
                            dado_atual = st.session_state.df.at[idx_orig, "detalhes"]

                            # --- BLOCO DE SEGURANÇA CONTRA ERRO SCALAR ---
                            try:
                                if isinstance(dado_atual, str):
                                    dados_json = json.loads(dado_atual)
                                else:
                                    dados_json = dado_atual

                                # Se não for uma lista (ex: for um texto solto ou número), força lista vazia
                                if not isinstance(dados_json, list):
                                    dados_json = []
                            except:
                                dados_json = []

                            # Só cria o DataFrame se houver itens
                            if dados_json:
                                df_itens_ia = pd.DataFrame(dados_json).fillna("")
                            else:
                                df_itens_ia = pd.DataFrame(columns=["descricao", "valor", "categoria", "natureza"])
                            # ---------------------------------------------

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