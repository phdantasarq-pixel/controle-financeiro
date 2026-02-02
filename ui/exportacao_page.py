import streamlit as st
from services.export_service import ExportService
from ui.components import seletor_meses_inteligente


def exportacao_page(df):
    st.header("📄 Exportação de Relatórios")

    mes_sel = seletor_meses_inteligente(key_suffix="export_page")
    m, a = map(int, mes_sel.split('/'))

    df_mes = df[(df['data_vencimento'].dt.month == m) & (df['data_vencimento'].dt.year == a)].copy()

    if df_mes.empty:
        st.warning("Sem dados para exportar neste mês.")
        return

    st.subheader("Configurações do Relatório")
    incluir_ia = st.toggle("Gerar Insights com IA", value=True)

    # --- Lógica de Insights (Regras Simples ou Chamada de API) ---
    insights_texto = "Seu balanço está positivo! Continue monitorando as despesas variáveis."
    if incluir_ia:
        total_desp = df_mes[df_mes['tipo'] == 'Despesa']['valor'].sum()
        total_rec = df_mes[df_mes['tipo'] == 'Receita']['valor'].sum()
        if total_desp > total_rec:
            insights_texto = "⚠️ Atenção: Suas despesas superaram as receitas. Sugerimos revisar custos fixos."
        elif total_desp > (total_rec * 0.8):
            insights_texto = "🟡 Alerta: Você está comprometendo mais de 80% da sua renda. Cuidado com novas compras."

    col1, col2 = st.columns(2)

    with col1:
        st.info("Relatório em Excel (.xlsx)")
        excel_data = ExportService.gerar_excel(df_mes)
        st.download_button(
            label="📥 Baixar Excel",
            data=excel_data,
            file_name=f"Relatorio_PlanejAI_{m}_{a}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with col2:
        st.info("Relatório em PDF (.pdf)")
        pdf_data = ExportService.gerar_pdf(df_mes, mes_sel, insights_texto)
        st.download_button(
            label="📥 Baixar PDF com Insights",
            data=pdf_data,
            file_name=f"Relatorio_PlanejAI_{m}_{a}.pdf",
            mime="application/pdf"
        )

    # Preview dos Insights
    st.divider()
    st.markdown(f"### 💡 Preview dos Insights\n{insights_texto}")