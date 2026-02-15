import streamlit as st
import pandas as pd
from services.export_service import ExportService
from ui.components import seletor_meses_inteligente


def exportacao_page(df):
    # --- CSS REFINADO (PADRÃO LUXURY DO PROJETO H8.1) ---
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
            .export-box {
                border: 1px solid rgba(255, 255, 255, 0.05);
                background: rgba(255, 255, 255, 0.01);
                padding: 20px;
                border-radius: 15px;
                margin-bottom: 10px;
                height: 100%;
            }
        </style>

        <div class="main-header">
            <div class="subtitle-main">Gerenciamento de Arquivos</div>
            <div class="title-main">Exportação de Relatórios</div>
            <div class="subtitle-main" style="color: rgba(255,255,255,0.4); letter-spacing: 1px; margin-top: 5px;">
                PlanejAI <span style="color: #3498db; font-weight: bold;">v8.1</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if df is None or df.empty:
        st.warning("⚠️ Não existem dados carregados para exportação.")
        return

    # 2. Preparação Técnica dos Dados
    df_clean = df.copy()
    df_clean['data_vencimento'] = pd.to_datetime(df_clean['data_vencimento'], errors='coerce')

    # 3. Seletor de Período
    mes_sel = seletor_meses_inteligente(key_suffix="export_page")

    try:
        m, a = map(int, mes_sel.split('/'))
    except ValueError:
        st.error("Formato de data inválido.")
        return

    # 4. Filtragem por Mês/Ano
    df_mes = df_clean[
        (df_clean['data_vencimento'].dt.month == m) &
        (df_clean['data_vencimento'].dt.year == a)
        ].copy()

    if df_mes.empty:
        st.info(f"📅 O período {mes_sel} não possui lançamentos.")
        return

    # --- AJUSTE DE COLUNAS (REMOÇÃO DE INTERFACE E LIXO TÉCNICO) ---
    colunas_ocultas = [
        '_id', 'id', 'id_parcelamento', 'parcela',
        'detalhes', 'lixeira', 'excluir', 'editar'
    ]

    df_export = df_mes.drop(columns=[c for c in colunas_ocultas if c in df_mes.columns])

    df_visual = df_export.copy()
    df_visual['data_vencimento'] = df_visual['data_vencimento'].dt.strftime('%d/%m/%Y')
    df_visual = df_visual.dropna(how='all')

    # Cálculos para Insights
    total_desp = df_mes[df_mes['tipo'].str.lower() == 'despesa']['valor'].sum() if 'tipo' in df_mes.columns else 0
    total_rec = df_mes[df_mes['tipo'].str.lower() == 'receita']['valor'].sum() if 'tipo' in df_mes.columns else 0

    st.divider()

    # 5. Configurações e Insights
    col_cfg, col_ins = st.columns([1, 1.5])
    with col_cfg:
        st.subheader("Configurações")
        incluir_ia = st.toggle("🧠 Gerar Insights com IA", value=True)

    with col_ins:
        insights_texto = "Seu balanço está positivo!"
        if incluir_ia:
            if total_desp > total_rec and total_rec > 0:
                insights_texto = "⚠️ Atenção: Suas despesas superaram as receitas."
            elif total_desp > (total_rec * 0.8) and total_rec > 0:
                insights_texto = "🟡 Alerta: Você está comprometendo mais de 80% da sua renda."
        st.info(f"**Análise da IA:** {insights_texto}")

    # 6. Botões de Download
    st.write("### ⬇️ Formatos Disponíveis")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="export-box">', unsafe_allow_html=True)
        st.write("📊 **Excel (.xlsx)**")
        try:
            excel_data = ExportService.gerar_excel(df_export)
            st.download_button(
                label="Baixar Planilha",
                data=excel_data,
                file_name=f"Relatorio_PlanejAI_{m}_{a}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="btn_excel"
            )
        except Exception as e:
            st.error(f"Erro Excel: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="export-box">', unsafe_allow_html=True)
        st.write("📄 **PDF Executivo**")
        try:
            # AJUSTE LOCAL: Garantindo bytes para evitar Erro de 'bytearray'
            pdf_raw = ExportService.gerar_pdf(df_export, mes_sel, insights_texto)
            pdf_bytes = bytes(pdf_raw)

            st.download_button(
                label="Baixar Relatório PDF",
                data=pdf_bytes,
                file_name=f"Relatorio_PlanejAI_{m}_{a}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary",
                key="btn_pdf"
            )
        except Exception as e:
            st.error(f"Erro PDF: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    # 7. Preview Final Limpo
    st.write("")
    with st.expander("👁️ Ver itens incluídos no relatório", expanded=False):
        st.dataframe(df_visual, use_container_width=True)