#!/bin/bash

echo "💎 Reiniciando PlanejAI com Limpeza Profunda (Bash Mode)..."

# 1. Removendo __pycache__ recursivamente
echo "🧹 Removendo __pycache__ de todas as pastas..."
find . -d -name "__pycache__" -exec rm -rf {} +

# 2. Limpando cache do Streamlit
echo "🧼 Limpando cache do Streamlit..."
streamlit cache clear

# 3. Matando processos antigos do Streamlit (Porta 8501)
echo "⚡ Liberando processos travados..."
# No Bash/Git Bash, tentamos encontrar o processo do python que roda o streamlit
pkill -f "streamlit run app.py" || echo "Nenhum processo anterior rodando."

# 4. Inicia o App
echo "🚀 Lançando PlanejAI..."
streamlit run app.py