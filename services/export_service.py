import pandas as pd
from fpdf import FPDF
import io
import os


class ExportService:
    @staticmethod
    def limpar_texto(texto):
        """Remove caracteres especiais para compatibilidade com PDF Latin-1."""
        if not texto: return ""
        return str(texto).encode('ascii', 'ignore').decode('ascii')

    @staticmethod
    def gerar_excel(df):
        """Gera Excel profissional com datas no padrão brasileiro (dd/mm/yyyy)."""
        output = io.BytesIO()

        # Criamos uma cópia para não afetar o DataFrame original do sistema
        df_export = df.copy()

        # Removemos o ID do MongoDB para o relatório ficar limpo
        if '_id' in df_export.columns:
            df_export = df_export.drop(columns=['_id'])

        # --- TRATAMENTO DE DATAS ---
        # Convertemos para datetime e garantimos que o Excel receba o objeto data puro
        for col in ['data_vencimento', 'data_registro']:
            if col in df_export.columns:
                df_export[col] = pd.to_datetime(df_export[col]).dt.date

        # Separação por tipo
        df_rec = df_export[df_export['tipo'] == 'Receita']
        df_desp = df_export[df_export['tipo'] == 'Despesa']

        total_rec = df_rec['valor'].sum()
        total_desp = df_desp['valor'].sum()
        saldo = total_rec - total_desp

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book

            # --- DEFINIÇÃO DE FORMATOS ---
            fmt_header = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1, 'align': 'center'})
            fmt_money = workbook.add_format({'num_format': 'R$ #,##0.00', 'border': 1})
            # Força o Excel a exibir no padrão brasileiro
            fmt_date = workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 1, 'align': 'center'})
            fmt_border = workbook.add_format({'border': 1})

            # --- ABA LANÇAMENTOS ---
            ws = workbook.add_worksheet('Lancamentos')
            writer.sheets['Lancamentos'] = ws

            # Cabeçalhos de seção
            ws.write(0, 0, f"RECEITAS (Total: R$ {total_rec:,.2f})",
                     workbook.add_format({'bold': True, 'font_color': 'green'}))
            df_rec.to_excel(writer, index=False, sheet_name='Lancamentos', startrow=1)

            start_row_desp = len(df_rec) + 4
            ws.write(start_row_desp - 1, 0, f"DESPESAS (Total: R$ {total_desp:,.2f})",
                     workbook.add_format({'bold': True, 'font_color': 'red'}))
            df_desp.to_excel(writer, index=False, sheet_name='Lancamentos', startrow=start_row_desp)

            # --- APLICAÇÃO DE FORMATOS NAS COLUNAS ---
            # Coluna A (Data Vencimento)
            ws.set_column('A:A', 15, fmt_date)
            # Coluna B (Descricao)
            ws.set_column('B:B', 45, fmt_border)
            # Coluna D (Valor)
            ws.set_column('D:D', 18, fmt_money)
            # Coluna F (Data Registro)
            ws.set_column('F:F', 15, fmt_date)

            # --- ABA RESUMO ---
            ws_res = workbook.add_worksheet('Resumo')
            ws_res.write(0, 0, 'INDICADOR', fmt_header)
            ws_res.write(0, 1, 'VALOR', fmt_header)

            ws_res.write(1, 0, 'Total Receitas', fmt_border)
            ws_res.write(1, 1, total_rec, fmt_money)

            ws_res.write(2, 0, 'Total Despesas', fmt_border)
            ws_res.write(2, 1, total_desp, fmt_money)

            cor_saldo = 'green' if saldo >= 0 else 'red'
            fmt_saldo = workbook.add_format(
                {'bold': True, 'num_format': 'R$ #,##0.00', 'font_color': cor_saldo, 'border': 1})

            ws_res.write(3, 0, 'SALDO LIQUIDO', fmt_header)
            ws_res.write(3, 1, saldo, fmt_saldo)
            ws_res.set_column('A:B', 25)

        return output.getvalue()

    @staticmethod
    def gerar_pdf(df, mes_referencia, insights=""):
        """Gera PDF mantendo o padrão original aprovado."""
        pdf = FPDF()
        pdf.add_page()

        # Título
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, "Relatorio Financeiro - PlanejAI", ln=True, align='C')
        pdf.set_font("Arial", '', 12)
        pdf.cell(190, 8, f"Periodo: {mes_referencia}", ln=True, align='C')
        pdf.ln(10)

        # Insights
        if insights:
            pdf.set_font("Arial", 'B', 11)
            pdf.set_fill_color(230, 240, 255)
            pdf.cell(190, 8, " Analise PlanejAI", ln=True, fill=True)
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(190, 6, ExportService.limpar_texto(insights))
            pdf.ln(5)

        # Tabelas (Receitas e Despesas)
        for tipo in ['Receita', 'Despesa']:
            df_tipo = df[df['tipo'] == tipo]
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(190, 10, f" {tipo}s", ln=True, fill=False)

            pdf.set_font("Arial", 'B', 9)
            pdf.cell(30, 8, "Vencimento", 1)
            pdf.cell(120, 8, "Descricao", 1)
            pdf.cell(40, 8, "Valor", 1)
            pdf.ln()

            pdf.set_font("Arial", '', 9)
            for _, row in df_tipo.iterrows():
                # Formatação BR no PDF também
                data_br = row['data_vencimento'].strftime('%d/%m/%Y')
                pdf.cell(30, 7, data_br, 1)
                pdf.cell(120, 7, ExportService.limpar_texto(row['descricao']), 1)
                pdf.cell(40, 7, f"R$ {row['valor']:,.2f}", 1)
                pdf.ln()
            pdf.ln(5)

        return pdf.output(dest='S').encode('latin-1')