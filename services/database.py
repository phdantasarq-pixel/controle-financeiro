import pandas as pd
import streamlit as st
from pymongo import MongoClient
from datetime import datetime


class Database:
    @staticmethod
    def conectar():
        """Estabelece a conexão com o MongoDB LOCAL."""
        try:
            uri = "mongodb://localhost:27017/"
            client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            client.admin.command('ping')
            return client["planejai"]
        except Exception as e:
            st.error(f"❌ Não consegui conectar ao MongoDB Local: {e}")
            st.info("Dica: Verifique se o serviço do MongoDB está iniciado (mongod).")
            return None

    @staticmethod
    def carregar_dados():
        """Carrega os lançamentos financeiros."""
        db = Database.conectar()
        if db is None:
            return pd.DataFrame()

        colecao = db["lancamentos"]
        dados = list(colecao.find())
        if not dados:
            return pd.DataFrame(
                columns=["data_vencimento", "data_registro", "tipo", "natureza", "valor", "categoria", "descricao"])

        df = pd.DataFrame(dados)
        if "_id" in df.columns:
            df = df.drop(columns=["_id"])

        # Garante que ao carregar, as datas sejam tratadas como datetime do Pandas
        if "data_vencimento" in df.columns:
            df["data_vencimento"] = pd.to_datetime(df["data_vencimento"], errors='coerce')

        return df

    @staticmethod
    def salvar_dados(df):
        """Salva os lançamentos financeiros com limpeza profunda de NaT e Timezones."""
        db = Database.conectar()
        if db is not None:
            colecao = db["lancamentos"]

            try:
                # 1. Se o DF estiver vazio, apenas limpa a coleção e sai
                if df.empty:
                    colecao.delete_many({})
                    return

                # 2. Criamos uma cópia para processamento
                df_para_salvar = df.copy()

                # 3. Limpeza de Datas (Onde o erro acontecia)
                for col in df_para_salvar.columns:
                    if pd.api.types.is_datetime64_any_dtype(df_para_salvar[col]):
                        # Remove Timezone (ajuda com o erro utcoffset)
                        if df_para_salvar[col].dt.tz is not None:
                            df_para_salvar[col] = df_para_salvar[col].dt.tz_localize(None)

                        # Converte NaT para None (Essencial para o MongoDB)
                        df_para_salvar[col] = df_para_salvar[col].astype(object).where(df_para_salvar[col].notnull(),
                                                                                       None)

                # 4. Converte para dicionário
                registros = df_para_salvar.to_dict("records")

                # 5. Operação Atômica: Deleta e Insere
                colecao.delete_many({})
                colecao.insert_many(registros)

            except Exception as e:
                st.error(f"⚠️ Erro ao processar dados para o MongoDB: {e}")

    @staticmethod
    def carregar_saldos():
        """Carrega os saldos gerais das contas."""
        db = Database.conectar()
        if db is None:
            return pd.DataFrame(columns=["conta", "valor"])

        dados = list(db["saldos_gerais"].find({}, {"_id": 0}))
        return pd.DataFrame(dados) if dados else pd.DataFrame(columns=["conta", "valor"])

    @staticmethod
    def salvar_saldos(df_saldos):
        """Salva os saldos gerais (sobrescreve a coleção)."""
        db = Database.conectar()
        if db is not None:
            try:
                db["saldos_gerais"].delete_many({})
                if not df_saldos.empty:
                    db["saldos_gerais"].insert_many(df_saldos.to_dict("records"))
            except Exception as e:
                st.error(f"⚠️ Erro ao salvar saldos: {e}")