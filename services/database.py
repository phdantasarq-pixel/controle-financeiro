import pandas as pd
import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import re

"""
Database Service
Responsável por:
- Conexão MongoDB
- Persistência de lançamentos financeiros
- Persistência de saldos
- Persistência de preferências do usuário

⚠️ Não contém lógica de UI
⚠️ Não contém regras visuais
"""

class Database:
    @staticmethod
    def conectar():
        """Estabelece a conexão com o MongoDB LOCAL."""
        try:
            # Mantendo a conexão local conforme sua branch develop
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
        """Carrega os lançamentos e garante a presença da coluna status e tipagem de data."""
        db = Database.conectar()
        if db is None: return pd.DataFrame()

        colecao = db["lancamentos"]
        dados = list(colecao.find())
        if not dados:
            return pd.DataFrame(
                columns=["data_vencimento", "data_registro", "tipo", "natureza", "valor", "categoria", "descricao",
                         "status"])

        df = pd.DataFrame(dados)

        # Garantia de Status (Essencial para o H8.1 Saldo em Tempo Real)
        if "status" not in df.columns:
            df["status"] = "Pendente"
        else:
            df["status"] = df["status"].fillna("Pendente")

        # Conversão de data para evitar erros no acessor .dt
        if "data_vencimento" in df.columns:
            df["data_vencimento"] = pd.to_datetime(df["data_vencimento"], errors='coerce')

        # Regra de negócio: Remover 'id' (UUID legado) se presente, mantendo apenas o _id do Mongo internamente
        if 'id' in df.columns:
            df = df.drop(columns=['id'])

        return df

    @staticmethod
    def atualizar_status(doc_id, novo_status):
        """Atualiza o status de um lançamento específico no MongoDB."""
        db = Database.conectar()
        if db is not None:
            try:
                from bson.objectid import ObjectId
                db["lancamentos"].update_one({"_id": ObjectId(doc_id)}, {"$set": {"status": novo_status}})
                return True
            except Exception as e:
                st.error(f"Erro ao atualizar status: {e}")
        return False

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

                # Tratamento de tipagem para compatibilidade MongoDB
                for col in df_para_salvar.columns:
                    if pd.api.types.is_datetime64_any_dtype(df_para_salvar[col]):
                        if df_para_salvar[col].dt.tz is not None:
                            df_para_salvar[col] = df_para_salvar[col].dt.tz_localize(None)
                        # Converte NaT para None (null no Mongo)
                        df_para_salvar[col] = df_para_salvar[col].astype(object).where(df_para_salvar[col].notnull(),
                                                                                       None)

                # Se houver a coluna interna do Mongo '_id', removemos para reinserção ou tratamos
                if '_id' in df_para_salvar.columns:
                    df_para_salvar = df_para_salvar.drop(columns=['_id'])

                registros = df_para_salvar.to_dict("records")
                colecao.delete_many({})  # Sobrescreve para manter sincronia com o DataFrame do State
                colecao.insert_many(registros)
            except Exception as e:
                st.error(f"⚠️ Erro ao processar dados para o MongoDB: {e}")

    # --- BLOCO DE SALDOS (H7.1 e H8.1) ---

    @staticmethod
    def carregar_saldos():
        """Carrega os saldos gerais das contas da coleção dedicada."""
        db = Database.conectar()
        if db is None:
            return pd.DataFrame(columns=["conta", "valor"])
        dados = list(db["saldos_gerais"].find({}, {"_id": 0}))
        return pd.DataFrame(dados) if dados else pd.DataFrame(columns=["conta", "valor"])

    @staticmethod
    def listar_contas():
        """Retorna os saldos no formato de lista para a resumo_page."""
        df_saldos = Database.carregar_saldos()
        if df_saldos.empty:
            return []
        # Garante que o valor seja numérico para somas na UI
        df_saldos['saldo'] = pd.to_numeric(df_saldos['valor'], errors='coerce').fillna(0)
        return df_saldos.to_dict("records")

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
    def obter_total_saldos_real():
        """Soma o valor de todas as contas em 'saldos_gerais'."""
        df_saldos = Database.carregar_saldos()
        if df_saldos.empty:
            return 0.0
        return pd.to_numeric(df_saldos['valor'], errors='coerce').sum()

    # --- IMPORTAÇÃO CUSTOMIZADA (Modelo Janeiro-2026.csv) ---

    @staticmethod
    def importar_do_csv(caminho_arquivo, mes, ano):
        """Lê o CSV do Excel e converte para o formato PlanejAI adaptado ao seu modelo."""
        try:
            # sep=None detecta automaticamente vírgula ou ponto e vírgula
            df_excel = pd.read_csv(caminho_arquivo, sep=None, engine='python').fillna(0)
            novos_lancamentos = []

            for _, row in df_excel.iterrows():
                desc = str(row.get('Descrição', ''))
                # Ignora cabeçalhos repetidos ou linhas de totalizador
                if desc in ['0', '', 'Descrição', 'Pessoa', 'A Receber'] or "Devendo" in desc:
                    continue

                def limpar_valor(val):
                    try:
                        if isinstance(val, str):
                            # Remove pontos de milhar e troca vírgula por ponto
                            val = val.replace('.', '').replace(',', '.')
                        return float(val)
                    except:
                        return 0.0

                v_divida = limpar_valor(row.get('Divida', 0))
                v_pago = limpar_valor(row.get('Pago', 0))

                # Se houver valor em dívida ou pago, assume o maior (lógica para seu modelo)
                valor_final = v_divida if v_divida > 0 else v_pago
                if valor_final == 0: continue

                # Extração inteligente do dia da coluna "Venc e Quantidade"
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

                # Categorização automática baseada em palavras-chave
                desc_lower = desc.lower()
                cat_final = "Outros"
                if any(x in desc_lower for x in ["cartão", "itau", "nubank", "caixa", "inter", "visa", "master"]):
                    cat_final = "Cartão de Crédito"
                elif any(x in desc_lower for x in ["emprestimo", "financiamento", "parcela", "bradesco", "embracon"]):
                    cat_final = "Empréstimo"
                elif any(x in desc_lower for x in
                         ["internet", "energia", "condominio", "seguro", "faculdade", "park", "bsparc"]):
                    cat_final = "Fixo Mensal"

                novos_lancamentos.append({
                    "data_vencimento": data_venc,
                    "data_registro": datetime.now().strftime('%Y-%m-%d'),
                    "tipo": "Despesa",
                    "natureza": "Fixo" if "dia" in texto_venc.lower() else "Variável",
                    "valor": valor_final,
                    "categoria": cat_final,
                    "descricao": desc,
                    "status": "Concluído" if v_pago > 0 else "Pendente"
                })

            if novos_lancamentos:
                df_importado = pd.DataFrame(novos_lancamentos)
                df_atual = Database.carregar_dados()

                # Concatena sem duplicar dados se necessário (lógica simples de append)
                df_combinado = pd.concat([df_atual, df_importado], ignore_index=True)
                Database.salvar_dados(df_combinado)
                return True
            return False
        except Exception as e:
            st.error(f"Erro na importação: {e}")
            return False

    # --- BLOCO DE PREFERÊNCIAS (NOVO - H10) ---

    @staticmethod
    def salvar_preferencias(cores):
        """Salva as cores do tema na coleção 'configuracoes' do MongoDB."""
        db = Database.conectar()
        if db is not None:
            try:
                db["configuracoes"].update_one(
                    {"_id": "tema_usuario"},
                    {"$set": {"cores": list(cores)}},
                    upsert=True
                )
            except Exception as e:
                st.error(f"Erro ao salvar preferências no banco: {e}")

    @staticmethod
    def carregar_preferencias():
        """Carrega as cores salvas. Retorna None se não houver configuração."""
        db = Database.conectar()
        if db is not None:
            config = db["configuracoes"].find_one({"_id": "tema_usuario"})
            if config and "cores" in config:
                return tuple(config["cores"])
        return None