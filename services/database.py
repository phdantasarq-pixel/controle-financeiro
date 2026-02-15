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
        """Carrega os lançamentos filtrados pelo usuário logado e garante a tipagem correta."""
        db = Database.conectar()
        if db is None:
            return pd.DataFrame()

        # Recupera o ID do usuário da sessão
        user_id = st.session_state.get('user_id')

        # Se por algum motivo não houver usuário logado, retorna vazio por segurança
        if not user_id:
            return pd.DataFrame(
                columns=["data_vencimento", "data_registro", "tipo", "natureza", "valor", "categoria", "descricao",
                         "status"]
            )

        colecao = db["lancamentos"]

        # FILTRO DE ISOLAMENTO: Busca apenas os documentos deste usuário
        query = {"user_id": user_id}
        dados = list(colecao.find(query))

        if not dados:
            return pd.DataFrame(
                columns=["data_vencimento", "data_registro", "tipo", "natureza", "valor", "categoria", "descricao",
                         "status"]
            )

        df = pd.DataFrame(dados)

        # --- REGRAS DE NEGÓCIO HOMOLOGADAS ---

        # Garantia de Status (Essencial para o [H8.1] Saldo em Tempo Real)
        if "status" not in df.columns:
            df["status"] = "🟡 Pendente"
        else:
            df["status"] = df["status"].fillna("🟡 Pendente")

        # Conversão de data para evitar erros no acessor .dt
        if "data_vencimento" in df.columns:
            df["data_vencimento"] = pd.to_datetime(df["data_vencimento"], errors='coerce')

        # Regra de negócio: Remover 'id' (UUID legado) mantendo apenas o _id do Mongo internamente
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
        """Salva os lançamentos financeiros garantindo o isolamento por usuário."""
        db = Database.conectar()
        if db is not None:
            colecao = db["lancamentos"]
            user_id = st.session_state.get('user_id')

            if not user_id:
                st.error("Erro: Usuário não identificado. Não é possível salvar.")
                return

            try:
                # 1. Limpa APENAS os dados deste usuário logado
                colecao.delete_many({"user_id": user_id})

                if df.empty:
                    return

                df_para_salvar = df.copy()

                # 2. Garante que todos os registros tenham o user_id antes de salvar
                df_para_salvar["user_id"] = user_id

                # Tratamento de tipagem (Mantendo sua lógica de NaT e Timezones)
                for col in df_para_salvar.columns:
                    if pd.api.types.is_datetime64_any_dtype(df_para_salvar[col]):
                        if df_para_salvar[col].dt.tz is not None:
                            df_para_salvar[col] = df_para_salvar[col].dt.tz_localize(None)
                        df_para_salvar[col] = df_para_salvar[col].astype(object).where(df_para_salvar[col].notnull(),
                                                                                       None)

                # Se houver a coluna interna do Mongo '_id', removemos para não dar erro de duplicidade
                if '_id' in df_para_salvar.columns:
                    df_para_salvar = df_para_salvar.drop(columns=['_id'])

                registros = df_para_salvar.to_dict("records")
                colecao.insert_many(registros)

            except Exception as e:
                st.error(f"⚠️ Erro ao processar dados para o MongoDB: {e}")

    # --- BLOCO DE SALDOS (H7.1 e H8.1) ---

    @staticmethod
    def carregar_saldos():
        """Carrega os saldos das contas filtrados pelo usuário logado."""
        db = Database.conectar()
        user_id = st.session_state.get('user_id')

        if db is None or not user_id:
            return pd.DataFrame(columns=["conta", "valor"])

        # Filtra apenas as contas do usuário logado
        dados = list(db["saldos_gerais"].find({"user_id": user_id}))

        if not dados:
            return pd.DataFrame(columns=["conta", "valor"])

        return pd.DataFrame(dados)

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
        """Salva os saldos gerais garantindo o isolamento por usuário."""
        db = Database.conectar()
        user_id = st.session_state.get('user_id')

        if db is not None and user_id:
            try:
                colecao = db["saldos_gerais"]
                # 1. Limpa apenas as contas deste usuário
                colecao.delete_many({"user_id": user_id})

                if not df_saldos.empty:
                    df_para_salvar = df_saldos.copy()
                    # 2. Garante o vínculo do user_id em cada conta
                    df_para_salvar["user_id"] = user_id

                    # Remove o _id antigo se existir para evitar conflitos de inserção
                    if '_id' in df_para_salvar.columns:
                        df_para_salvar = df_para_salvar.drop(columns=['_id'])

                    colecao.insert_many(df_para_salvar.to_dict("records"))
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
                    "user_id": st.session_state.user_id,  # O vínculo crucial
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
        db = Database.conectar()
        user_id = st.session_state.get('user_id')  # Busca o dono do tema
        if db is not None and user_id:
            db["configuracoes"].update_one(
                {"user_id": user_id},  # Filtra pelo usuário
                {"$set": {"cores": list(cores)}},
                upsert=True
            )

    @staticmethod
    def carregar_preferencias():
        db = Database.conectar()
        user_id = st.session_state.get('user_id')
        if db is not None and user_id:
            config = db["configuracoes"].find_one({"user_id": user_id})
            if config and "cores" in config:
                return tuple(config["cores"])
        return None

    @staticmethod
    def inserir_muitos(lista_registros):
        db = Database.conectar()
        user_id = st.session_state.get('user_id')

        if db is not None and lista_registros:
            try:
                colecao = db["lancamentos"]
                for reg in lista_registros:
                    # Garante o vínculo do usuário em cada registro clonado
                    reg["user_id"] = user_id

                    if isinstance(reg.get('data_vencimento'), pd.Timestamp):
                        reg['data_vencimento'] = reg['data_vencimento'].to_pydatetime()

                colecao.insert_many(lista_registros)
                return True
            except Exception as e:
                st.error(f"⚠️ Erro ao inserir novos registros: {e}")
        return False
    @staticmethod
    def buscar_usuario(email):
        """Busca um usuário na coleção 'usuarios' pelo email."""
        try:
            # Acesse a coleção 'usuarios' (ajuste o nome se necessário)
            db = Database.conectar()
            return db.usuarios.find_one({"email": email})
        except Exception as e:
            print(f"Erro ao buscar usuário: {e}")
            return None

    @staticmethod
    def criar_usuario(nome, email, senha):
        try:
            db = Database.conectar()
            # Verifica se o email já existe
            if db.usuarios.find_one({"email": email}):
                return False, "Este e-mail já está cadastrado."

            novo_usuario = {
                "nome": nome,
                "email": email,
                "senha": senha,  # No futuro, aplicaremos hash aqui
                "data_cadastro": datetime.now(),
                "preferencias": {
                    "tema": "Luxury",
                    "cores": ["#4facfe", "#FFFFFF", "#050608", "#0d1b2a"]
                }
            }
            db.usuarios.insert_one(novo_usuario)
            return True, "Usuário criado com sucesso!"
        except Exception as e:
            return False, f"Erro ao conectar ao banco: {e}"