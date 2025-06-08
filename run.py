import uvicorn
import nltk
import os
import spacy
from pathlib import Path

def download_resources():
    """Download necessary resources for NLP processing"""
    print("Verificando recursos necessários...")
    
    # Download NLTK resources
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("Baixando recursos do NLTK...")
        nltk.download('punkt')
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')
    
    # Check if spaCy model is installed
    try:
        nlp = spacy.load("pt_core_news_lg")
        print("Modelo spaCy já está instalado.")
    except OSError:
        print("Instalando modelo spaCy...")
        os.system("python -m spacy download pt_core_news_lg")

if __name__ == "__main__":
    # Obter o diretório atual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ensure data directory exists
    data_dir = os.path.join(current_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Download necessary resources
    download_resources()
    
    # Importar e executar setup do ambiente
    try:
        from setup import setup_environment
        setup_environment()
    except ImportError:
        print("Módulo setup não encontrado. Pulando configuração automática.")
    
    # Run the API server (quando executado dentro da pasta api)
    print("Iniciando servidor API...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 