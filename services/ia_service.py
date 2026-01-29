import google.generativeai as genai
import streamlit as st
import pandas as pd


class IAService:
    def __init__(self):
        self.api_key = st.secrets.get("GEMINI_API_KEY")
        self.model = None

        if not self.api_key:
            st.error("Chave não encontrada.")
            return

        try:
            # Forçamos a configuração
            genai.configure(api_key=self.api_key)

            # --- MANOBRA DE AUTO-DESCOBERTA ---
            # Vamos listar os modelos que sua chave REALMENTE pode ver
            available_models = [m.name for m in genai.list_models() if
                                'generateContent' in m.supported_generation_methods]

            # Prioridade de escolha
            preferencia = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']

            modelo_escolhido = None
            for p in preferencia:
                if p in available_models:
                    modelo_escolhido = p
                    break

            # Se não achou na lista de preferência, pega o primeiro disponível
            if not modelo_escolhido and available_models:
                modelo_escolhido = available_models[0]

            if modelo_escolhido:
                self.model = genai.GenerativeModel(modelo_escolhido)
                # Teste silencioso
                self.model.generate_content("oi", generation_config={"max_output_tokens": 1})
            else:
                st.error("Nenhum modelo compatível encontrado para esta chave.")

        except Exception as e:
            st.error(f"Erro ao listar modelos: {e}")

    def gerar_insight(self, df: pd.DataFrame, mes_atual: str):
        if not self.model:
            return "O cérebro da IA não conseguiu mapear os modelos disponíveis."

        # Limpeza para o prompt
        df_limpo = df.copy()
        cols_drop = [c for c in ['_id', 'id', 'data_registro'] if c in df_limpo.columns]
        df_limpo = df_limpo.drop(columns=cols_drop)

        prompt = f"Como consultor PlanejAI, analise: {df_limpo.to_csv(index=False)}"

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Erro na análise: {str(e)}"