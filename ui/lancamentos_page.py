import streamlit as st
from datetime import date, datetime
import pandas as pd

# Imports de serviço e componentes
try:
    from services.ia_service import IAService
    from services.database import Database
    from ui.components import seletor_meses_inteligente
except Exception as e:
    st.error(f"Erro ao carregar dependências: {e}")


def lancamentos_page(df_atual):
    st.header("➕ Gerenciar Lançamentos")

    # --- [H10] SELETOR DE MÊS (Retornado para a página) ---
    mes_ref = seletor_meses_inteligente(key_suffix="pg_lanc_ia")
    # Converte o mês selecionado (MM/YYYY) para um objeto datetime para usar nos lançamentos
    data_selecionada = datetime.strptime(mes_ref, "%m/%Y")

    # Inicializa o serviço de IA
    try:
        ia = IAService()
    except:
        ia = None

    # --- ABAS DE ENTRADA ---
    tab_manual, tab_ia = st.tabs(["📝 Lançamento Manual", "🤖 Importar Fatura (IA)"])

    # --- ABA 1: LANÇAMENTO MANUAL ---
    with tab_manual:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                # O valor padrão agora respeita o seletor de meses
                data_base = st.date_input("Vencimento", value=data_selecionada, format="DD/MM/YYYY")
                tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
                valor = st.number_input("Valor R$", min_value=0.0, step=0.01)
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
                        "valor": valor,
                        "categoria": categoria,
                        "descricao": descricao,
                        "status": "🟡 Pendente"
                    }])
                    st.session_state.df = pd.concat([st.session_state.df, novo_dado], ignore_index=True)
                    Database.salvar_dados(st.session_state.df)
                    st.success("Salvo com sucesso!")
                    st.rerun()

    # --- ABA 2: IMPORTAÇÃO POR IA ---
    with tab_ia:
        st.subheader("🤖 Importação Gemini")
        st.caption(f"Os itens serão registrados em: **{mes_ref}**")

        if ia is None:
            st.warning("IA não configurada. Verifique suas chaves de API.")
        else:
            arquivo = st.file_uploader("Subir Fatura", type=["pdf", "png", "jpg", "jpeg"])

            if arquivo:
                if st.button("✨ Analisar Fatura com Gemini"):
                    with st.spinner("Lendo dados..."):
                        itens = ia.processar_fatura(arquivo)
                        if itens:
                            st.session_state.preview_fatura = itens
                            st.rerun()

            if "preview_fatura" in st.session_state:
                st.write("### 🔍 Conferência")
                df_preview = pd.DataFrame(st.session_state.preview_fatura)
                st.dataframe(df_preview, use_container_width=True)

                c_btn1, c_btn2 = st.columns(2)
                if c_btn1.button("📥 Confirmar Importação", use_container_width=True):
                    novos_itens = []
                    for item in st.session_state.preview_fatura:
                        novos_itens.append({
                            "data_vencimento": pd.to_datetime(data_selecionada),  # Usa o mês do seletor
                            "data_registro": datetime.now().strftime('%Y-%m-%d'),
                            "tipo": "Despesa",
                            "natureza": "Variável",
                            "valor": item["valor"],
                            "categoria": item.get("categoria", "Cartão de Crédito"),
                            "descricao": item["descricao"],
                            "status": "🟡 Pendente"
                        })

                    df_novos = pd.DataFrame(novos_itens)
                    st.session_state.df = pd.concat([st.session_state.df, df_novos], ignore_index=True)
                    Database.salvar_dados(st.session_state.df)
                    del st.session_state.preview_fatura
                    st.success(f"Fatura importada para {mes_ref}!")
                    st.rerun()

                if c_btn2.button("❌ Cancelar", use_container_width=True):
                    del st.session_state.preview_fatura
                    st.rerun()

    # --- LISTAGEM ---
    st.divider()
    st.subheader(f"📋 Lançamentos de {mes_ref}")

    # Filtra a listagem para mostrar apenas o mês selecionado no seletor
    if not df_atual.empty:
        df_atual['data_vencimento'] = pd.to_datetime(df_atual['data_vencimento'])
        mask = (df_atual['data_vencimento'].dt.month == data_selecionada.month) & \
               (df_atual['data_vencimento'].dt.year == data_selecionada.year)
        df_mes = df_atual[mask].iloc[::-1]

        if not df_mes.empty:
            for idx, row in df_mes.iterrows():
                cols = st.columns([3, 2, 2, 1])
                cols[0].write(f"**{row['descricao']}**")
                cols[1].write(f"R$ {row['valor']:,.2f}")
                cols[2].write(f"{row['status']}")
                if cols[3].button("🗑️", key=f"del_{idx}"):
                    st.session_state.df = st.session_state.df.drop(idx)
                    Database.salvar_dados(st.session_state.df)
                    st.rerun()
        else:
            st.info(f"Nenhum lançamento para {mes_ref}.")