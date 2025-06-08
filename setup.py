import nltk
import spacy
import os
import joblib
import json
from pathlib import Path

def setup_environment():
    """
    Configura o ambiente de execução baixando recursos necessários
    """
    print("Configurando ambiente de execução...")
    
    # Obter o diretório atual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Baixar recursos do NLTK
    print("Baixando recursos do NLTK...")
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    
    # Verificar se o modelo spaCy está instalado
    try:
        print("Verificando modelo spaCy...")
        nlp = spacy.load("pt_core_news_lg")
        print("Modelo spaCy carregado com sucesso!")
    except:
        print("Instalando modelo spaCy...")
        os.system("python -m spacy download pt_core_news_lg")
    
    # Verificar se os modelos joblib existem
    modelo_aspectos_path = os.path.join(current_dir, "modelo_aspectos.joblib")
    modelo_sentimentos_path = os.path.join(current_dir, "modelo_sentimentos.joblib")
    
    if not os.path.exists(modelo_aspectos_path) or not os.path.exists(modelo_sentimentos_path):
        print("AVISO: Modelos de ML não encontrados. Criando modelos padrão...")
        
        # Criar um modelo simples caso os modelos não estejam disponíveis
        from sklearn.pipeline import Pipeline
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        
        # Modelo de aspectos
        if not os.path.exists(modelo_aspectos_path):
            print("Criando modelo de aspectos padrão...")
            modelo_aspectos = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=10000, ngram_range=(1, 2))),
                ('classifier', LogisticRegression(max_iter=1000))
            ])
            # Treinar com dados mínimos
            X = ["economia brasil", "congresso nacional", "governo federal", "outros assuntos"]
            y = [0, 1, 2, 3]
            modelo_aspectos.fit(X, y)
            joblib.dump(modelo_aspectos, modelo_aspectos_path)
            print(f"Modelo de aspectos salvo em {modelo_aspectos_path}")
        
        # Modelo de sentimentos
        if not os.path.exists(modelo_sentimentos_path):
            print("Criando modelo de sentimentos padrão...")
            modelo_sentimentos = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=10000, ngram_range=(1, 2))),
                ('classifier', LogisticRegression(max_iter=1000))
            ])
            # Treinar com dados mínimos
            X = ["muito bom", "neutro", "muito ruim"]
            y = [0, 1, 2]
            modelo_sentimentos.fit(X, y)
            joblib.dump(modelo_sentimentos, modelo_sentimentos_path)
            print(f"Modelo de sentimentos salvo em {modelo_sentimentos_path}")
    
    # Verificar mapeamento de labels
    label_mappings_path = os.path.join(current_dir, "label_mappings.json")
    if not os.path.exists(label_mappings_path):
        print("Criando mapeamento de labels padrão...")
        label_mappings = {
            "aspects": {
                "economia": 0,
                "congresso": 1,
                "governo": 2,
                "outros": 3
            },
            "sentiments": {
                "positivo": 0,
                "neutro": 1,
                "negativo": 2
            }
        }
        with open(label_mappings_path, 'w', encoding='utf-8') as f:
            json.dump(label_mappings, f, ensure_ascii=False, indent=2)
        print(f"Mapeamento de labels salvo em {label_mappings_path}")
    
    # Criar pasta data se não existir
    data_dir = os.path.join(current_dir, "data")
    if not os.path.exists(data_dir):
        print(f"Criando diretório de dados em {data_dir}")
        os.makedirs(data_dir, exist_ok=True)
    
    print("Configuração do ambiente concluída!")

if __name__ == "__main__":
    setup_environment() 