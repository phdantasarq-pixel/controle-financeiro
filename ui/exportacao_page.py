import streamlit as st
import pandas as pd
from services.export_service import ExportService
from ui.components import seletor_meses_inteligente


def exportacao_page(df):
    st.header("📄 Exportação de Relatórios")

    # 1. Verificação de Integridade dos Dados
    if df is None or df.empty:
        st.warning("⚠️ Não existem dados carregados para exportação. Importe um arquivo ou adicione lançamentos.")
        return

    # 2. Preparação dos Dados (Garantindo tipagem e removendo IDs)
    df_clean = df.copy()

    # Garante que data_vencimento é datetime para o filtro funcionar
    df_clean['data_vencimento'] = pd.to_datetime(df_clean['data_vencimento'], errors='coerce')

    # Remove colunas de ID para o relatório não exibir lixo técnico (Regra PlanejAI)
    colunas_para_remover = ['_id', 'id']
    df_clean = df_clean.drop(columns=[c for c in colunas_para_remover if c in df_clean.columns])

    # 3. Seletor de Período
    mes_sel = seletor_meses_inteligente(key_suffix="export_page")
    try:
        m, a = map(int, mes_sel.split('/'))
    except ValueError:
        st.error("Formato de data inválido no seletor.")
        return

    # 4. Filtragem por Mês/Ano
    df_mes = df_clean[
        (df_clean['data_vencimento'].dt.month == m) &
        (df_clean['data_vencimento'].dt.year == a)
        ].copy()

    if df_mes.empty:
        st.warning(f"Sem dados para exportar em {mes_sel}.")
        return

    st.subheader("Configurações do Relatório")
    incluir_ia = st.toggle("Gerar Insights com IA", value=True)

    # 5. Lógica de Insights Baseada em Dados Reais
    insights_texto = "Seu balanço está positivo! Continue monitorando as despesas variáveis."

    # Cálculo de métricas para os insights
    total_desp = df_mes[df_mes['tipo'].str.lower() == 'despesa']['valor'].sum() if 'tipo' in df_mes.columns else 0
    total_rec = df_mes[df_mes['tipo'].str.lower() == 'receita']['valor'].sum() if 'tipo' in df_mes.columns else 0

    if incluir_ia:
        if total_desp > total_rec and total_rec > 0:
            insights_texto = "⚠️ Atenção: Suas despesas superaram as receitas. Sugerimos revisar custos fixos."
        elif total_desp > (total_rec * 0.8) and total_rec > 0:
            insights_texto = "🟡 Alerta: Você está comprometendo mais de 80% da sua renda. Cuidado com novas compras."
        elif total_rec == 0 and total_desp > 0:
            insights_texto = "ℹ️ Apenas despesas registradas. Certifique-se de lançar suas receitas para um balanço completo."

    # 6. Botões de Download
    col1, col2 = st.columns(2)

    with col1:
        st.info("Relatório em Excel (.xlsx)")
        try:
            excel_data = ExportService.gerar_excel(df_mes)
            st.download_button(
                label="📥 Baixar Excel",
                data=excel_data,
                file_name=f"Relatorio_PlanejAI_{m}_{a}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="btn_excel"
            )
        except Exception as e:
            st.error(f"Erro ao gerar Excel: {e}")

    with col2:
        st.info("Relatório em PDF (.pdf)")
        try:
            # O ExportService deve estar preparado para receber o texto de insights
            pdf_data = ExportService.gerar_pdf(df_mes, mes_sel, insights_texto)
            st.download_button(
                label="📥 Baixar PDF com Insights",
                data=pdf_data,
                file_name=f"Relatorio_PlanejAI_{m}_{a}.pdf",
                mime="application/pdf",
                key="btn_pdf"
            )
        except Exception as e:
            st.error(f"Erro ao gerar PDF: {e}")

    # 7. Preview para o Usuário
    st.divider()
    with st.expander("👁️ Visualizar dados selecionados", expanded=False):
        st.dataframe(df_mes, use_container_width=True)

    st.markdown(f"### 💡 Insights do Período\n> {insights_texto}")