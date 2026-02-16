import json
import urllib.parse
from pymongo import MongoClient, ASCENDING, DESCENDING
from bson import ObjectId
from datetime import datetime

# =====================================================
# 1. CONFIGURAÇÃO (DADOS FORNECIDOS)
# =====================================================
USUARIO = "admin_planejai"
SENHA = "Ph818324@"
# Extraído da sua URL: cluster0.bgqysvm.mongodb.net
CLUSTER_URL = "cluster0.bgqysvm.mongodb.net"
DB_NAME = "planejai_db"

# Tratamento para caracteres especiais na senha (como o @)
senha_codificada = urllib.parse.quote_plus(SENHA)

# Montagem da URI seguindo o padrão SRV do Atlas
MONGO_URI_CLOUD = f"mongodb+srv://{USUARIO}:{senha_codificada}@{CLUSTER_URL}/?retryWrites=true&w=majority&appName=Cluster0"

print(f"🔗 Conectando ao MongoDB Atlas em: {CLUSTER_URL}...")

try:
    client = MongoClient(MONGO_URI_CLOUD)
    db = client[DB_NAME]
    # Teste de conexão real
    client.admin.command('ping')
    print("✅ Conexão estabelecida com sucesso!")
except Exception as e:
    print(f"❌ Erro crítico de conexão: {e}")
    exit()


# =====================================================
# 2. FUNÇÃO DE MIGRAÇÃO
# =====================================================
def migrate_collection(file_name, collection_name):
    print(f"\n📦 Migrando coleção: {collection_name}")
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Limpa a coleção na NUVEM antes de inserir (evita duplicar em caso de re-execução)
        db[collection_name].delete_many({})

        # Tratamento de dados para compatibilidade com MongoDB (ID e Datas)
        for item in data:
            # Converte IDs de string/dict para ObjectId real
            if '_id' in item:
                if isinstance(item['_id'], dict) and '$oid' in item['_id']:
                    item['_id'] = ObjectId(item['_id']['$oid'])
                elif isinstance(item['_id'], str):
                    # Para casos como 'tema_usuario' que são strings fixas
                    pass

            # Converte campos de data do formato JSON exportado para Datetime do Python
            for campo_data in ['data_vencimento', 'data_cadastro', 'data_registro']:
                if campo_data in item:
                    valor = item[campo_data]
                    if isinstance(valor, dict) and '$date' in valor:
                        # Trata formato ISO vindo do MongoDB Export
                        dt_str = valor['$date'].replace('Z', '+00:00')
                        item[campo_data] = datetime.fromisoformat(dt_str)
                    elif isinstance(valor, str) and len(valor) <= 10:
                        # Trata datas simples "YYYY-MM-DD"
                        try:
                            item[campo_data] = datetime.strptime(valor, "%Y-%m-%d")
                        except:
                            pass

        if data:
            db[collection_name].insert_many(data)
            print(f"✔️ {len(data)} registros enviados para {collection_name}.")
        else:
            print(f"⚠️ Coleção {collection_name} estava vazia nos arquivos.")

    except FileNotFoundError:
        print(f"⚠️ Aviso: Arquivo {file_name} não encontrado. Pulando...")
    except Exception as e:
        print(f"❌ Erro ao processar {collection_name}: {e}")


# =====================================================
# 3. CRIAÇÃO DE ÍNDICES (PARA VELOCIDADE NA NUVEM)
# =====================================================
def create_indexes():
    print("\n⚡ Otimizando banco com índices...")

    # Índice para buscas de lançamentos (user + data)
    db.lancamentos.create_index([("user_id", ASCENDING), ("data_vencimento", DESCENDING)])

    # Índice único para login (não permite emails duplicados)
    db.usuarios.create_index([("email", ASCENDING)], unique=True)

    # Índice para saldos por conta
    db.saldos_gerais.create_index([("user_id", ASCENDING), ("conta", ASCENDING)])

    print("🚀 Índices criados com sucesso!")


# =====================================================
# EXECUÇÃO PRINCIPAL
# =====================================================
if __name__ == "__main__":
    # Lista de arquivos JSON que você enviou
    arquivos_para_migrar = {
        'planejai.lancamentos.json': 'lancamentos',
        'planejai.usuarios.json': 'usuarios',
        'planejai.saldos_gerais.json': 'saldos_gerais',
        'planejai.configuracoes.json': 'configuracoes'
    }

    for arquivo, colecao in arquivos_para_migrar.items():
        migrate_collection(arquivo, colecao)

    create_indexes()

    print("\n💎 PROCESSO FINALIZADO!")
    print("Seus dados agora estão seguros no MongoDB Atlas Cloud.")