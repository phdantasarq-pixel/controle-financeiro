import pandas as pd
from fpdf import FPDF
import io
import os
import matplotlib.pyplot as plt


class ExportService:
    @staticmethod
    def limpar_texto(texto):
        """Remove caracteres especiais para compatibilidade com PDF Latin-1."""
        if not texto: return ""
        # fpdf2 lida melhor com unicode, mas manter o encode/decode garante estabilidade
        return str(texto).encode('latin-1', 'ignore').decode('latin-1')

    @staticmethod
    def gerar_excel(df):
        """Gera Excel profissional com datas no padrão brasileiro."""
        output = io.BytesIO()
        df_export = df.copy()

        if '_id' in df_export.columns:
            df_export = df_export.drop(columns=['_id'])

        for col in ['data_vencimento', 'data_registro']:
            if col in df_export.columns:
                df_export[col] = pd.to_datetime(df_export[col]).dt.date

        df_rec = df_export[df_export['tipo'] == 'Receita']
        df_desp = df_export[df_export['tipo'] == 'Despesa']

        total_rec = df_rec['valor'].sum()
        total_desp = df_desp['valor'].sum()
        saldo = total_rec - total_desp

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            fmt_header = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1, 'align': 'center'})
            fmt_money = workbook.add_format({'num_format': 'R$ #,##0.00', 'border': 1})
            fmt_date = workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 1, 'align': 'center'})
            fmt_border = workbook.add_format({'border': 1})

            ws = workbook.add_worksheet('Lancamentos')
            ws.write(0, 0, f"RECEITAS (Total: R$ {total_rec:,.2f})",
                     workbook.add_format({'bold': True, 'font_color': 'green'}))
            df_rec.to_excel(writer, index=False, sheet_name='Lancamentos', startrow=1)

            start_row_desp = len(df_rec) + 4
            ws.write(start_row_desp - 1, 0, f"DESPESAS (Total: R$ {total_desp:,.2f})",
                     workbook.add_format({'bold': True, 'font_color': 'red'}))
            df_desp.to_excel(writer, index=False, sheet_name='Lancamentos', startrow=start_row_desp)

            ws.set_column('A:A', 15, fmt_date)
            ws.set_column('B:B', 45, fmt_border)
            ws.set_column('D:D', 18, fmt_money)

            ws_res = workbook.add_worksheet('Resumo')
            ws_res.write(0, 0, 'INDICADOR', fmt_header)
            ws_res.write(0, 1, 'VALOR', fmt_header)
            ws_res.write(1, 0, 'Total Receitas', fmt_border)
            ws_res.write(1, 1, total_rec, fmt_money)
            ws_res.write(2, 0, 'Total Despesas', fmt_border)
            ws_res.write(2, 1, total_desp, fmt_money)

            fmt_saldo = workbook.add_format(
                {'bold': True, 'num_format': 'R$ #,##0.00', 'font_color': 'green' if saldo >= 0 else 'red',
                 'border': 1})
            ws_res.write(3, 0, 'SALDO LIQUIDO', fmt_header)
            ws_res.write(3, 1, saldo, fmt_saldo)
            ws_res.set_column('A:B', 25)

        return output.getvalue()

    @staticmethod
    def gerar_pdf(df, mes_referencia, insights=""):
        """Gera PDF corrigido para fpdf2 com totalizadores e gráficos."""
        # --- CÁLCULOS DOS TOTALIZADORES ---
        total_rec = df[df['tipo'] == 'Receita']['valor'].sum()
        total_desp = df[df['tipo'] == 'Despesa']['valor'].sum()
        saldo = total_rec - total_desp

        pdf = FPDF()
        pdf.add_page()

        # Header Luxury
        pdf.set_font("Arial", 'B', 18)
        pdf.set_text_color(49, 51, 63)
        pdf.cell(190, 15, "RELATÓRIO FINANCEIRO - PlanejAI", ln=True, align='C')
        pdf.set_font("Arial", '', 11)
        pdf.cell(190, 5, f"Período de Referência: {mes_referencia}", ln=True, align='C')
        pdf.ln(10)

        # --- BLOCO DE TOTALIZADORES (Cards Visual) ---
        pdf.set_fill_color(240, 242, 246)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(60, 10, " TOTAL RECEITAS", 1, 0, 'L', fill=True)
        pdf.cell(65, 10, " TOTAL DESPESAS", 1, 0, 'L', fill=True)
        pdf.cell(65, 10, " SALDO LÍQUIDO", 1, 1, 'L', fill=True)

        pdf.set_font("Arial", '', 12)
        pdf.set_text_color(0, 128, 0)  # Verde
        pdf.cell(60, 12, f" R$ {total_rec:,.2f}", 1, 0, 'L')
        pdf.set_text_color(200, 0, 0)  # Vermelho
        pdf.cell(65, 12, f" R$ {total_desp:,.2f}", 1, 0, 'L')

        cor_saldo = (0, 128, 0) if saldo >= 0 else (200, 0, 0)
        pdf.set_text_color(*cor_saldo)
        pdf.cell(65, 12, f" R$ {saldo:,.2f}", 1, 1, 'L')
        pdf.set_text_color(0, 0, 0)  # Reset para preto
        pdf.ln(10)

        # --- GRÁFICO DE COMPOSIÇÃO ---
        if total_rec > 0 or total_desp > 0:
            plt.figure(figsize=(6, 3))
            plt.pie([total_rec, total_desp], labels=['Receitas', 'Despesas'],
                    colors=['#4CAF50', '#FF5252'], autopct='%1.1f%%', startangle=140)
            plt.title("Composição Financeira")

            img_buf = io.BytesIO()
            plt.savefig(img_buf, format='png', bbox_inches='tight')
            img_buf.seek(0)
            pdf.image(img_buf, x=60, w=90)
            plt.close()
            pdf.ln(5)

        # Insights
        if insights:
            pdf.set_font("Arial", 'B', 11)
            pdf.set_fill_color(230, 240, 255)
            pdf.cell(190, 8, " Análise Inteligente", ln=True, fill=True)
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(190, 6, ExportService.limpar_texto(insights))
            pdf.ln(5)

        # Tabelas
        for tipo in ['Receita', 'Despesa']:
            df_tipo = df[df['tipo'] == tipo]
            if df_tipo.empty: continue

            pdf.set_font("Arial", 'B', 12)
            pdf.cell(190, 10, f" Detalhamento de {tipo}s", ln=True)

            pdf.set_font("Arial", 'B', 9)
            pdf.set_fill_color(200, 200, 200)
            pdf.cell(30, 8, " Vencimento", 1, 0, 'L', fill=True)
            pdf.cell(120, 8, " Descrição", 1, 0, 'L', fill=True)
            pdf.cell(40, 8, " Valor", 1, 1, 'L', fill=True)

            pdf.set_font("Arial", '', 9)
            for _, row in df_tipo.iterrows():
                dt = row['data_vencimento'].strftime('%d/%m/%Y') if hasattr(row['data_vencimento'],
                                                                            'strftime') else str(row['data_vencimento'])
                pdf.cell(30, 7, f" {dt}", 1)
                pdf.cell(120, 7, f" {ExportService.limpar_texto(row['descricao'])}", 1)
                pdf.cell(40, 7, f" R$ {row['valor']:,.2f}", 1, 1)
            pdf.ln(5)

        # CORREÇÃO DEFINITIVA DO BYTEARRAY:
        # No fpdf2, output() sem argumentos retorna um bytearray.
        # Converter para bytes() resolve o erro do Streamlit.
        return bytes(pdf.output())