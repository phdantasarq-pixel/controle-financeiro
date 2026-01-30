import pandas as pd
import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import re


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
        """Carrega os lançamentos financeiros do MongoDB."""
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
                if df.empty:
                    colecao.delete_many({})
                    return

                df_para_salvar = df.copy()

                # Limpeza de Datas para compatibilidade com MongoDB BSON
                for col in df_para_salvar.columns:
                    if pd.api.types.is_datetime64_any_dtype(df_para_salvar[col]):
                        # Remove Timezone (evita erro utcoffset)
                        if df_para_salvar[col].dt.tz is not None:
                            df_para_salvar[col] = df_para_salvar[col].dt.tz_localize(None)

                        # Converte NaT (Pandas) para None (Python/Mongo)
                        df_para_salvar[col] = df_para_salvar[col].astype(object).where(df_para_salvar[col].notnull(),
                                                                                       None)

                registros = df_para_salvar.to_dict("records")

                # Operação de sobrescrita atômica
                colecao.delete_many({})
                colecao.insert_many(registros)

            except Exception as e:
                st.error(f"⚠️ Erro ao processar dados para o MongoDB: {e}")

    @staticmethod
    def carregar_saldos():
        """Carrega os saldos gerais das contas (H7.1)."""
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

    @staticmethod
    def importar_do_csv(caminho_arquivo, mes, ano):
        """Lê o CSV do Excel e converte para o formato PlanejAI com categorização inteligente."""
        try:
            df_excel = pd.read_csv(caminho_arquivo).fillna(0)

            novos_lancamentos = []
            for _, row in df_excel.iterrows():
                desc = str(row.get('Descrição', ''))

                # Pula linhas irrelevantes
                if desc in ['0', '', 'Descrição', 'Pessoa', 'A Receber'] or "Devendo" in desc:
                    continue

                # Tratamento numérico robusto
                def limpar_valor(val):
                    try:
                        if isinstance(val, str):
                            val = val.replace('.', '').replace(',', '.')
                        return float(val)
                    except:
                        return 0.0

                v_divida = limpar_valor(row.get('Divida', 0))
                v_pago = limpar_valor(row.get('Pago', 0))
                valor_final = v_divida if v_divida > 0 else v_pago

                if valor_final == 0:
                    continue

                # Extração do dia de vencimento via Regex
                dia = 10
                texto_venc = str(row.get('Venc e Quantidade', ''))
                numeros = re.findall(r'\d+', texto_venc)
                if numeros:
                    dia_ext = int(numeros[0])
                    dia = dia_ext if 1 <= dia_ext <= 28 else 10

                try:
                    data_venc = datetime(ano, mes, dia)
                except:
                    data_venc = datetime(ano, mes, 1)

                # --- CATEGORIZAÇÃO INTELIGENTE (NOVAS CATEGORIAS) ---
                desc_lower = desc.lower()
                cat_final = "Importado"

                if any(x in desc_lower for x in ["cartão", "itau", "nubank", "caixa", "inter", "visa", "master"]):
                    cat_final = "Cartão de Crédito"
                elif any(x in desc_lower for x in ["emprestimo", "financiamento", "parcela", "bradesco"]):
                    cat_final = "Empréstimo"
                elif any(x in desc_lower for x in ["internet", "energia", "condominio", "seguro", "faculdade"]):
                    cat_final = "Fixo Mensal"

                novos_lancamentos.append({
                    "data_vencimento": data_venc,
                    "data_registro": datetime.now().strftime('%Y-%m-%d'),
                    "tipo": "Despesa",
                    "natureza": "Fixo" if "fixo" in texto_venc.lower() else "Variável",
                    "valor": valor_final,
                    "categoria": cat_final,
                    "descricao": desc
                })

            if novos_lancamentos:
                df_final = pd.DataFrame(novos_lancamentos)
                df_atual = Database.carregar_dados()

                # Opcional: Remover duplicatas do mesmo mês antes de anexar
                # df_atual = df_atual[~((df_atual['data_vencimento'].dt.month == mes) & (df_atual['data_vencimento'].dt.year == ano))]

                df_combinado = pd.concat([df_atual, df_final], ignore_index=True)
                Database.salvar_dados(df_combinado)
                return True
            return False
        except Exception as e:
            st.error(f"Erro na importação: {e}")
            return False