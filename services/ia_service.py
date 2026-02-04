import google.generativeai as genai
import streamlit as st
import pandas as pd
import json
import os

class IAService:
    def __init__(self):
        self.api_key = st.secrets.get("GEMINI_API_KEY")
        self.model = None

        if not self.api_key:
            st.error("Chave da API não configurada.")
            return

        try:
            genai.configure(api_key=self.api_key)
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            preferencia = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
            modelo_escolhido = next((p for p in preferencia if p in available_models),
                                    available_models[0] if available_models else None)

            if modelo_escolhido:
                self.model = genai.GenerativeModel(modelo_escolhido)
            else:
                st.error("Nenhum modelo compatível encontrado.")
        except Exception as e:
            st.error(f"Erro ao inicializar IA: {e}")

    def processar_fatura(self, arquivo):
        if not self.model:
            st.error("Modelo de IA não carregado.")
            return {"emissor": "Cartão", "vencimento": None, "itens": []}

        try:
            arquivo_bytes = arquivo.read()
            mime_type = arquivo.type
            arquivo.seek(0)

            # PROMPT ATUALIZADO PARA CAPTURAR PARCELAS
            prompt = """
                        Você é um especialista em contabilidade e análise de faturas do sistema PlanejAI.
                        Analise o documento e extraia TODOS os gastos para garantir que a soma final seja idêntica ao total da fatura.

                        REGRAS DE EXTRAÇÃO:
                        1. IDENTIFIQUE O EMISSOR: Nome do banco ou instituição.
                        2. DATA DE VENCIMENTO: Localize a data de vencimento (YYYY-MM-DD). Se não houver ano, use 2026.
                        3. ITENS E VALORES: Extraia TODAS as linhas de débito, incluindo compras, taxas, IOF, juros e anuidades. Ignore apenas pagamentos de fatura e créditos.
                        4. DESCRIÇÃO E PARCELAS: 
                           - Mantenha a descrição legível.
                           - Se houver indicação de parcelamento (ex: "01/10", "1 de 5", "x3") no texto original, extraia EXATAMENTE esse texto para o campo "parcela".
                           - Se não houver menção de parcela no item, deixe o campo "parcela" vazio ("").
                        5. CATEGORIZAÇÃO: Use EXATAMENTE: [Moradia, Alimentação, Transporte, Lazer, Saúde, Educação, Assinaturas, Cartão de Crédito, Outro].
                        6. PRECISÃO: Não arredonde valores antes da soma. O valor deve ser o número real com 2 casas decimais.

                        RETORNO OBRIGATÓRIO (JSON PURO, SEM MARKDOWN):
                        {
                            "emissor": "Nome do Banco",
                            "vencimento": "YYYY-MM-DD",
                            "itens": [
                                {
                                    "descricao": "Nome do Estabelecimento ou Taxa", 
                                    "valor": 12.50, 
                                    "categoria": "Categoria", 
                                    "parcela": "1/10", 
                                    "data": "2026-02-03"
                                }
                            ]
                        }
                        """

            conteudo = [{"mime_type": mime_type, "data": arquivo_bytes}, prompt]
            response = self.model.generate_content(conteudo)

            json_text = response.text.strip()
            if "```" in json_text:
                json_text = json_text.split("```")[1]
                if json_text.startswith("json"):
                    json_text = json_text[4:]

            dados_extraidos = json.loads(json_text)

            if "itens" in dados_extraidos:
                for item in dados_extraidos["itens"]:
                    item["valor"] = round(float(item["valor"]), 2)
                    # Garante que o campo parcela exista mesmo se vazio
                    if "parcela" not in item:
                        item["parcela"] = ""

            return dados_extraidos

        except Exception as e:
            st.error(f"Erro no processamento da IA: {str(e)}")
            return {"emissor": "Cartão", "vencimento": None, "itens": []}

    def gerar_insight(self, contexto: dict, mes_atual: str, indicadores: dict = None):
        """ Gera análise estratégica baseada em lançamentos e saldos. """
        if not self.model: return "IA indisponível."

        df_l = contexto.get("lancamentos", pd.DataFrame())
        # Remove campos internos para não confundir a IA
        colunas_remover = ['_id', 'id', 'detalhes']
        df_l_limpo = df_l.drop(columns=[c for c in colunas_remover if c in df_l.columns]).tail(30)

        txt_indicadores = ""
        if indicadores:
            txt_indicadores = f"""
            - Saldo Real: R$ {indicadores.get('saldo_contas', 0):,.2f}
            - Saldo Livre Projetado: R$ {indicadores.get('saldo_projetado', 0):,.2f}
            """

        prompt = f"""
        Você é o Consultor Estratégico do PlanejAI. Analise os dados financeiros abaixo:
        Mês de Referência: {mes_atual}
        {txt_indicadores}
        Últimos Lançamentos: 
        {df_l_limpo.to_csv(index=False)}

        Dê 3 dicas curtas, objetivas e encorajadoras sobre como economizar ou gerir o saldo este mês.
        """

        try:
            return self.model.generate_content(prompt).text
        except:
            return "Erro ao gerar análise financeira."

    def chat(self, mensagem_usuario, contexto, indicadores: dict = None):
        """ Responde dúvidas do usuário sobre o sistema ou finanças. """
        if not self.model: return "IA indisponível."

        info = f"Saldo Projetado: R$ {indicadores.get('saldo_projetado', 0):,.2f}" if indicadores else ""
        prompt = f"Você é o assistente inteligente do PlanejAI. {info}. Responda de forma clara: {mensagem_usuario}"

        try:
            return self.model.generate_content(prompt).text
        except:
            return "Desculpe, tive um problema ao processar sua pergunta agora."