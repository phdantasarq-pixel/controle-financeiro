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
                PlanejAI <span style="color: #3498db; font-weight: bold;">v8.1</span>
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
                    novo_dado = pd.DataFrame([{
                        "data_vencimento": pd.to_datetime(data_base),
                        "data_registro": datetime.now().strftime('%Y-%m-%d'),
                        "tipo": tipo_manual, "natureza": natureza, "valor": round(float(valor), 2),
                        "categoria": categoria, "descricao": descricao,
                        "status": "🟡 Pendente", "detalhes": None, "parcela": parcela_input
                    }])
                    st.session_state.df = pd.concat([st.session_state.df, novo_dado], ignore_index=True)
                    Database.salvar_dados(st.session_state.df)
                    st.toast("Sucesso!", icon="✅")
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
                                if "natureza" not in item: item["natureza"] = "Variável"
                            st.session_state.preview_fatura = resultado
                            st.rerun()

            if "preview_fatura" in st.session_state:
                st.markdown('<div class="ia-section-card">', unsafe_allow_html=True)
                dados_ia = st.session_state.preview_fatura
                emissor = dados_ia.get("emissor", "Cartão")
                st.write(f"### Conferência: {emissor}")

                df_editavel = st.data_editor(
                    pd.DataFrame(dados_ia["itens"]),
                    column_config={
                        "excluir": st.column_config.CheckboxColumn("🗑️", default=False),
                        "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                        "categoria": st.column_config.SelectboxColumn("Categoria", options=LISTA_CATEGORIAS),
                        "natureza": st.column_config.SelectboxColumn("Natureza", options=OPCOES_NATUREZA)
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
                             "original_index"]],
                    hide_index=True, use_container_width=True,
                    column_config={
                        "🗑️": st.column_config.CheckboxColumn("🗑️", default=False),
                        "Situacao": st.column_config.SelectboxColumn("Status", options=["🟢 Concluído", "🟡 Pendente",
                                                                                        "🔴 Atrasado"]),
                        "data_vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
                        "natureza": st.column_config.SelectboxColumn("Natureza", options=OPCOES_NATUREZA),
                        "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                        "categoria": st.column_config.SelectboxColumn("Categoria", options=LISTA_CATEGORIAS),
                        "original_index": None
                    },
                    key=f"editor_{tipo}"
                )
                if st.form_submit_button("💾 Salvar Alterações", use_container_width=True, type="primary"):
                    itens_excluir = df_editado[df_editado["🗑️"] == True]["original_index"].tolist()
                    if itens_excluir: st.session_state.df = st.session_state.df.drop(itens_excluir)
                    for _, row in df_editado.iterrows():
                        idx = row["original_index"]
                        if idx not in itens_excluir:
                            st.session_state.df.loc[
                                idx, ["status", "data_vencimento", "descricao", "natureza", "categoria", "valor"]] = \
                                [row["Situacao"], pd.to_datetime(row["data_vencimento"]), row["descricao"],
                                 row["natureza"], row["categoria"], row["valor"]]
                    Database.salvar_dados(st.session_state.df)
                    st.rerun()

            # --- DETALHAMENTO IA EM ABAS (RESTAURADO) ---
            if tipo == "Despesa":
                df_ia = df_tipo[df_tipo['detalhes'].notna() & (df_tipo['detalhes'] != "")]
                if not df_ia.empty:
                    st.markdown("---")
                    st.markdown('🔍 **Detalhamento de Itens das Faturas (IA)**')
                    titulos_abas = [f"📦 {row['descricao']}" for _, row in df_ia.iterrows()]
                    abas_faturas = st.tabs(titulos_abas)

                    for i, (idx_orig, row_f) in enumerate(df_ia.iterrows()):
                        with abas_faturas[i]:
                            dado_atual = st.session_state.df.at[idx_orig, "detalhes"]
                            df_itens_ia = pd.DataFrame(
                                json.loads(dado_atual) if isinstance(dado_atual, str) else dado_atual)

                            ed_ia = st.data_editor(
                                df_itens_ia, hide_index=True, use_container_width=True,
                                key=f"ed_ia_{idx_orig}",
                                column_config={
                                    "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                                    "categoria": st.column_config.SelectboxColumn("Categoria",
                                                                                  options=LISTA_CATEGORIAS),
                                    "natureza": st.column_config.SelectboxColumn("Natureza", options=OPCOES_NATUREZA)
                                }
                            )
                            if st.button(f"Atualizar {row_f['descricao']}", key=f"btn_ia_{idx_orig}"):
                                st.session_state.df.at[idx_orig, "detalhes"] = json.dumps(ed_ia.to_dict('records'))
                                Database.salvar_dados(st.session_state.df)
                                st.rerun()