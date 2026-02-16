import pandas as pd
import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import re
from bson import ObjectId
import sys

"""
Database Service - PlanejAI [Cloud Edition]
Responsável por:
- Conexão MongoDB Atlas (Nuvem)
- Isolamento de dados por user_id
- Persistência de lançamentos, saldos e preferências
"""

class Database:

    # 1. Mudança para garantir que a conexão seja recuperada corretamente
    _db = None

    @classmethod
    def get_db(cls):
        if cls._db is None:
            cls._db = cls.conectar()
        return cls._db

    @staticmethod
    def conectar():
        """Estabelece a conexão exclusivamente com o MongoDB ATLAS (Nuvem)."""
        try:
            if "mongo" in st.secrets:
                uri = st.secrets["mongo"]["uri"]
                db_name = st.secrets["mongo"].get("db_name", "planejai_db")
            else:
                st.error("❌ Configurações [mongo] não encontradas no secrets.toml!")
                st.stop()

            client = MongoClient(
                uri,
                serverSelectionTimeoutMS=10000,
                appName="PlanejAI_Cloud"
            )
            client.admin.command('ping')
            return client[db_name]
        except Exception as e:
            st.error(f"❌ Falha na conexão com MongoDB Atlas: {e}")
            st.info("💡 Verifique se o IP 0.0.0.0/0 está liberado no painel do MongoDB Atlas.")
            st.stop()

    # Inicialização da conexão global do serviço
    db = conectar.__func__()

    @staticmethod
    def carregar_dados():
        """Carrega os lançamentos filtrados estritamente pelo usuário logado (String ou ObjectId)."""
        db = Database.get_db()
        if db is None: return pd.DataFrame()

        user_id = st.session_state.get('user_id')

        if not user_id:
            return pd.DataFrame(
                columns=["data_vencimento", "data_registro", "tipo", "natureza", "valor", "categoria", "descricao",
                         "status"])

        colecao = db["lancamentos"]

        # --- AJUSTE CRÍTICO: FILTRO HÍBRIDO ---
        # Isso garante que ele ache os dados se o ID estiver como String OU como ObjectId no Atlas
        query = {
            "$or": [
                {"user_id": user_id},
                {"user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id}
            ]
        }

        dados = list(colecao.find(query))

        if not dados:
            return pd.DataFrame(
                columns=["data_vencimento", "data_registro", "tipo", "natureza", "valor", "categoria", "descricao",
                         "status"])

        df = pd.DataFrame(dados)

        # Limpeza de segurança: ajustada para o filtro híbrido
        if "user_id" in df.columns:
            # Converte a coluna para string para facilitar a comparação de segurança
            df["user_id_str"] = df["user_id"].apply(lambda x: str(x))
            df = df[df["user_id_str"] == str(user_id)]
            del df["user_id_str"]

        # Remove campos internos do Mongo
        if "_id" in df.columns: del df["_id"]

        return df

    @staticmethod
    def atualizar_status(doc_id, novo_status):
        """Atualiza o status de um lançamento específico na nuvem."""
        if Database.db is not None:
            try:
                from bson.objectid import ObjectId
                Database.db["lancamentos"].update_one(
                    {"_id": ObjectId(doc_id)},
                    {"$set": {"status": novo_status}}
                )
                return True
            except Exception as e:
                st.error(f"Erro ao atualizar status: {e}")
        return False

    @staticmethod
    def salvar_dados(df):
        """Salva os lançamentos financeiros garantindo o isolamento por usuário."""
        if Database.db is not None:
            colecao = Database.db["lancamentos"]
            user_id = st.session_state.get('user_id')

            if not user_id:
                st.error("Erro: Usuário não identificado.")
                return

            try:
                colecao.delete_many({"user_id": user_id})
                if df.empty: return

                df_para_salvar = df.copy()
                df_para_salvar["user_id"] = user_id

                for col in df_para_salvar.columns:
                    if pd.api.types.is_datetime64_any_dtype(df_para_salvar[col]):
                        if df_para_salvar[col].dt.tz is not None:
                            df_para_salvar[col] = df_para_salvar[col].dt.tz_localize(None)
                        df_para_salvar[col] = df_para_salvar[col].astype(object).where(df_para_salvar[col].notnull(), None)

                if '_id' in df_para_salvar.columns:
                    df_para_salvar = df_para_salvar.drop(columns=['_id'])

                registros = df_para_salvar.to_dict("records")
                colecao.insert_many(registros)
            except Exception as e:
                st.error(f"⚠️ Erro ao processar dados para o MongoDB Cloud: {e}")

    # --- BLOCO DE SALDOS ---

    @staticmethod
    def carregar_saldos():
        """Carrega os saldos das contas filtrados pelo usuário logado."""
        user_id = st.session_state.get('user_id')
        if Database.db is None or not user_id:
            return pd.DataFrame(columns=["conta", "valor"])

        dados = list(Database.db["saldos_gerais"].find({"user_id": user_id}))
        if not dados:
            return pd.DataFrame(columns=["conta", "valor"])

        return pd.DataFrame(dados)

    @staticmethod
    def listar_contas():
        """Retorna os saldos no formato de lista para a UI."""
        df_saldos = Database.carregar_saldos()
        if df_saldos.empty: return []
        df_saldos['saldo'] = pd.to_numeric(df_saldos['valor'], errors='coerce').fillna(0)
        return df_saldos.to_dict("records")

    @staticmethod
    def salvar_saldos(df_saldos):
        """Salva os saldos gerais garantindo o isolamento por usuário."""
        user_id = st.session_state.get('user_id')
        if Database.db is not None and user_id:
            try:
                colecao = Database.db["saldos_gerais"]
                colecao.delete_many({"user_id": user_id})

                if not df_saldos.empty:
                    df_para_salvar = df_saldos.copy()
                    df_para_salvar["user_id"] = user_id
                    if '_id' in df_para_salvar.columns:
                        df_para_salvar = df_para_salvar.drop(columns=['_id'])
                    colecao.insert_many(df_para_salvar.to_dict("records"))
            except Exception as e:
                st.error(f"⚠️ Erro ao salvar saldos na nuvem: {e}")

    @staticmethod
    def obter_total_saldos_real():
        """Soma o valor de todas as contas em 'saldos_gerais'."""
        df_saldos = Database.carregar_saldos()
        if df_saldos.empty: return 0.0
        return pd.to_numeric(df_saldos['valor'], errors='coerce').sum()

    # --- USUÁRIOS E PREFERÊNCIAS ---

    @staticmethod
    def buscar_usuario(email):
        """Busca um usuário pelo email na nuvem."""
        if Database.db is not None:
            return Database.db.usuarios.find_one({"email": email})
        return None

    @staticmethod
    def criar_usuario(nome, email, senha):
        """Cria um novo usuário na nuvem."""
        if Database.db is None: return False, "Banco offline"
        try:
            if Database.db.usuarios.find_one({"email": email}):
                return False, "E-mail já cadastrado."

            novo_usuario = {
                "nome": nome,
                "email": email,
                "senha": senha,
                "data_cadastro": datetime.now(),
                "preferencias": {
                    "tema": "Luxury",
                    "cores": ["#4facfe", "#FFFFFF", "#050608", "#0d1b2a"]
                }
            }
            Database.db.usuarios.insert_one(novo_usuario)
            return True, "Usuário criado com sucesso!"
        except Exception as e:
            return False, f"Erro ao criar usuário: {e}"

    @staticmethod
    def salvar_preferencias(cores):
        """Salva as cores do tema Luxury do usuário."""
        user_id = st.session_state.get('user_id')
        if Database.db is not None and user_id:
            Database.db["configuracoes"].update_one(
                {"user_id": user_id},
                {"$set": {"cores": list(cores)}},
                upsert=True
            )

    @staticmethod
    def carregar_preferencias():
        """Carrega as preferências de cores do usuário."""
        user_id = st.session_state.get('user_id')
        if Database.db is not None and user_id:
            config = Database.db["configuracoes"].find_one({"user_id": user_id})
            if config and "cores" in config:
                return tuple(config["cores"])
        return None

    @staticmethod
    def inserir_muitos(lista_registros):
        """Insere vários registros (usado para clonar meses)."""
        user_id = st.session_state.get('user_id')
        if Database.db is not None and lista_registros:
            try:
                for reg in lista_registros:
                    reg["user_id"] = user_id
                    if isinstance(reg.get('data_vencimento'), pd.Timestamp):
                        reg['data_vencimento'] = reg['data_vencimento'].to_pydatetime()
                Database.db["lancamentos"].insert_many(lista_registros)
                return True
            except Exception as e:
                st.error(f"⚠️ Erro ao clonar registros: {e}")
        return False

    # --- IMPORTAÇÃO CUSTOMIZADA ---

    @staticmethod
    def importar_do_csv(caminho_arquivo, mes, ano):
        """Importação de CSV conforme modelo PlanejAI."""
        try:
            df_excel = pd.read_csv(caminho_arquivo, sep=None, engine='python').fillna(0)
            novos_lancamentos = []
            user_id = st.session_state.get('user_id')

            for _, row in df_excel.iterrows():
                desc = str(row.get('Descrição', ''))
                if desc in ['0', '', 'Descrição', 'Pessoa', 'A Receber'] or "Devendo" in desc:
                    continue

                def limpar_valor(val):
                    try:
                        if isinstance(val, str):
                            val = val.replace('.', '').replace(',', '.')
                        return float(val)
                    except: return 0.0

                v_divida = limpar_valor(row.get('Divida', 0))
                v_pago = limpar_valor(row.get('Pago', 0))
                valor_final = v_divida if v_divida > 0 else v_pago
                if valor_final == 0: continue

                # Lógica de dia extraído do texto
                dia = 10
                texto_venc = str(row.get('Venc e Quantidade', ''))
                numeros = re.findall(r'\d+', texto_venc)
                if numeros:
                    dia_ext = int(numeros[0])
                    dia = dia_ext if 1 <= dia_ext <= 28 else 10

                data_venc = datetime(ano, mes, dia)
                desc_lower = desc.lower()
                cat_final = "Outros"
                if any(x in desc_lower for x in ["cartão", "itau", "nubank", "caixa", "inter", "visa", "master"]):
                    cat_final = "Cartão de Crédito"
                elif any(x in desc_lower for x in ["emprestimo", "financiamento", "parcela", "bradesco", "embracon"]):
                    cat_final = "Empréstimo"
                elif any(x in desc_lower for x in ["internet", "energia", "condominio", "seguro", "faculdade", "park", "bsparc"]):
                    cat_final = "Fixo Mensal"

                novos_lancamentos.append({
                    "user_id": user_id,
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
                df_combinado = pd.concat([df_atual, df_importado], ignore_index=True)
                Database.salvar_dados(df_combinado)
                return True
            return False
        except Exception as e:
            st.error(f"Erro na importação: {e}")
            return False