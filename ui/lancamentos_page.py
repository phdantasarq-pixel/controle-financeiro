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

    # --- [H10] SELETOR DE MÊS ---
    mes_ref = seletor_meses_inteligente(key_suffix="pg_lanc_ia")
    data_selecionada = datetime.strptime(mes_ref, "%m/%Y")

    try:
        ia = IAService()
    except:
        ia = None

    # --- ABAS ---
    tab_manual, tab_ia = st.tabs(["📝 Lançamento Manual", "🤖 Importar Fatura (IA)"])

    # --- ABA 1: MANUAL (MANTIDA) ---
    with tab_manual:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                data_base = st.date_input("Vencimento", value=data_selecionada, format="DD/MM/YYYY")
                tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
                valor = st.number_input("Valor R$", min_value=0.0, step=0.01, format="%.2f")
            with c2:
                natureza = st.selectbox("Natureza", ["Fixo", "Variável"])
                categoria = st.selectbox("Categoria",
                                         ["Moradia", "Alimentação", "Transporte", "Lazer", "Saúde", "Educação",
                                          "Assinaturas", "Salário", "Investimentos", "Cartão de Crédito", "Outro"])

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
                        "detalhes": None  # Importante inicializar vazio
                    }])
                    st.session_state.df = pd.concat([st.session_state.df, novo_dado], ignore_index=True)
                    Database.salvar_dados(st.session_state.df)
                    st.success("Salvo com sucesso!")
                    st.rerun()

    # --- ABA 2: IMPORTAÇÃO IA ---
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

                # Lógica de data
                venc_ia = dados_ia.get("vencimento")
                data_final_vencimento = pd.to_datetime(venc_ia) if venc_ia else pd.to_datetime(data_selecionada)

                df_p = pd.DataFrame(itens)
                total_f = df_p['valor'].sum()
                nome_f = f"Fatura {emissor} - {data_final_vencimento.strftime('%m/%y')}"

                with st.container(border=True):
                    st.markdown(f"#### {nome_f}")
                    st.write(f"🏦 Banco: **{emissor}** | 📅 Vencimento: **{data_final_vencimento.strftime('%d/%m/%Y')}**")
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
                        "detalhes": json.dumps(itens)  # Salvando como String JSON
                    }])
                    st.session_state.df = pd.concat([st.session_state.df, novo_reg], ignore_index=True)
                    Database.salvar_dados(st.session_state.df)
                    del st.session_state.preview_fatura
                    st.rerun()

    # --- LISTAGEM (O CORAÇÃO DO PROBLEMA) ---
    st.divider()
    st.subheader(f"📋 Lançamentos de {mes_ref}")

    if not df_atual.empty:
        df_temp = df_atual.copy()
        df_temp['data_vencimento'] = pd.to_datetime(df_temp['data_vencimento'])

        mask = (df_temp['data_vencimento'].dt.month == data_selecionada.month) & \
               (df_temp['data_vencimento'].dt.year == data_selecionada.year)
        df_mes = df_temp[mask].iloc[::-1]

        for idx, row in df_mes.iterrows():
            # --- TRATAMENTO ULTRA-ROBUSTO DO CAMPO DETALHES ---
            detalhes_brutos = row.get('detalhes', None)
            lista_itens = []

            # 1. Checa se não é nulo/nan
            if pd.notna(detalhes_brutos) and detalhes_brutos:
                try:
                    # 2. Se for string, descompacta o JSON
                    if isinstance(detalhes_brutos, str):
                        lista_itens = json.loads(detalhes_brutos)
                    # 3. Se já for uma lista (vinda direto do MongoDB como objeto)
                    elif isinstance(detalhes_brutos, list):
                        lista_itens = detalhes_brutos
                except:
                    lista_itens = []

            with st.container(border=True):
                c = st.columns([3, 2, 2, 0.5])

                # Se identificou itens, mostra o robô
                nome_exibicao = f"🤖 {row['descricao']}" if len(lista_itens) > 0 else row['descricao']

                c[0].write(f"**{nome_exibicao}**")
                c[1].write(f"R$ {float(row['valor']):,.2f}")
                c[2].write(f"{row['status']}")

                if c[3].button("🗑️", key=f"del_{idx}"):
                    st.session_state.df = st.session_state.df.drop(idx)
                    Database.salvar_dados(st.session_state.df)
                    st.rerun()

                # --- O EXPANSOR ---
                if len(lista_itens) > 0:
                    with st.expander("🔍 Ver itens detalhados"):
                        # Formata a tabelinha interna
                        df_detalhes = pd.DataFrame(lista_itens)
                        st.dataframe(df_detalhes, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado.")