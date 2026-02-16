#!/bin/bash

echo "💎 Reiniciando PlanejAI com Limpeza Profunda (Bash Mode)..."

# 1. Removendo __pycache__ de todas as pastas
find . -d -name "__pycache__" -exec rm -rf {} +

# 2. Limpando cache do Streamlit
streamlit cache clear

# 3. Matando processos antigos (Streamlit e Python)
pkill -f "streamlit run app.py" || echo "Nenhum processo anterior rodando."

# 4. FORÇAR ABERTURA NO CHROME
# O comando 'start' do Windows funciona no Git Bash para abrir o navegador
echo "🌐 Abrindo PlanejAI no Google Chrome..."
start chrome "http://localhost:8501"

# 5. Inicia o App
echo "🚀 Lançando PlanejAI..."
streamlit run app.py --server.headless true